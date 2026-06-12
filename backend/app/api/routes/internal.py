from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Iterator

from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import build_auth_error
from app.models.schema import IntegrationSettings, SyncLog, SyncProvider, SyncStatus
from app.repositories.queries import get_db_session
from app.services.recalculation_service import RecalculationSummary, recalculate_competition_state, recalculate_from_sync_request
from app.services.sync_service import SyncService, resolve_sync_log_provider

router = APIRouter(prefix="/api/internal", tags=["internal"])

AUTO_SYNC_LOCK_KEY = 2026061101


class InternalSyncResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    status: str
    operation: str
    message: str
    recalculation: RecalculationSummary | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_bearer_token(value: str | None) -> str | None:
    if value is None:
        return None
    prefix = "Bearer "
    if not value.startswith(prefix):
        return None
    token = value[len(prefix):].strip()
    return token or None


def _get_integration_settings(db_session: Session) -> IntegrationSettings | None:
    return db_session.scalar(
        select(IntegrationSettings).order_by(IntegrationSettings.updated_at.desc(), IntegrationSettings.id.desc())
    )


def _latest_auto_sync_log(db_session: Session) -> SyncLog | None:
    return db_session.scalar(
        select(SyncLog)
        .where(SyncLog.operation == "automatic_sync")
        .order_by(SyncLog.created_at.desc(), SyncLog.id.desc())
    )


@contextmanager
def _advisory_lock(db_session: Session) -> Iterator[bool]:
    if db_session.bind is None or db_session.bind.dialect.name != "postgresql":
        yield True
        return

    acquired = bool(
        db_session.execute(
            text("SELECT pg_try_advisory_lock(:key)"),
            {"key": AUTO_SYNC_LOCK_KEY},
        ).scalar()
    )
    try:
        yield acquired
    finally:
        if acquired:
            db_session.execute(
                text("SELECT pg_advisory_unlock(:key)"),
                {"key": AUTO_SYNC_LOCK_KEY},
            )


def _record_summary_log(
    db_session: Session,
    *,
    status_value: SyncStatus,
    result_code: str,
    message: str,
    payload: dict[str, object],
) -> None:
    db_session.add(
        SyncLog(
            provider=resolve_sync_log_provider(db_session, SyncProvider.THE_SPORTS_DB),
            status=status_value,
            operation="automatic_sync",
            match_id=None,
            created_by_user_id=None,
            result_code=result_code,
            message=message,
            payload=payload,
        )
    )
    db_session.flush()


@router.post("/sync/auto", response_model=InternalSyncResponse, status_code=status.HTTP_200_OK)
def trigger_auto_sync(
    authorization: str | None = Header(default=None),
    db_session: Session = Depends(get_db_session),
) -> InternalSyncResponse:
    settings = get_settings()
    expected_token = settings.sync_admin_token.get_secret_value().strip() if settings.sync_admin_token is not None else ""
    if not expected_token:
        raise build_auth_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="sync_admin_token_missing",
            message="SYNC_ADMIN_TOKEN is not configured",
        )

    submitted_token = _get_bearer_token(authorization)
    if submitted_token != expected_token:
        raise build_auth_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_sync_token",
            message="Authorization token is invalid",
        )

    integration_settings = _get_integration_settings(db_session)
    if integration_settings is None or not integration_settings.auto_sync_enabled:
        return InternalSyncResponse(
            provider=SyncProvider.THE_SPORTS_DB.value,
            status=SyncStatus.SKIPPED.value,
            operation="automatic_sync",
            message="Automatic sync is disabled",
            recalculation=None,
        )

    now = utc_now()
    latest_log = _latest_auto_sync_log(db_session)
    if latest_log is not None:
        next_due_at = latest_log.created_at + timedelta(minutes=integration_settings.auto_sync_interval_minutes)
        if next_due_at > now:
            return InternalSyncResponse(
                provider=SyncProvider.THE_SPORTS_DB.value,
                status=SyncStatus.SKIPPED.value,
                operation="automatic_sync",
                message=f"Automatic sync is not due until {next_due_at.isoformat()}",
                recalculation=None,
            )

    with _advisory_lock(db_session) as acquired:
        if not acquired:
            return InternalSyncResponse(
                provider=SyncProvider.THE_SPORTS_DB.value,
                status=SyncStatus.SKIPPED.value,
                operation="automatic_sync",
                message="Another automatic sync is already running",
                recalculation=None,
            )

        service = SyncService()
        try:
            sync_result = service.run_scheduled_sync(
                db_session,
                requested_provider=SyncProvider.THE_SPORTS_DB,
                allow_google_sheets_fallback=False,
                include_top_scorers=False,
                recalculation_hook=recalculate_from_sync_request,
                respect_timing_window=False,
            )
            recalculation = recalculate_competition_state(db_session)
        except Exception as exc:
            _record_summary_log(
                db_session,
                status_value=SyncStatus.FAILURE,
                result_code="automatic_sync_failed",
                message=str(exc),
                payload={
                    "provider": SyncProvider.THE_SPORTS_DB.value,
                    "interval_minutes": integration_settings.auto_sync_interval_minutes,
                },
            )
            db_session.commit()
            raise

        status_value = SyncStatus.SUCCESS if sync_result.failure_count == 0 else SyncStatus.FAILURE
        message = (
            f"Automatic sync completed with {sync_result.success_count} success(es), "
            f"{sync_result.skipped_count} skip(s), and {sync_result.failure_count} failure(s)"
        )
        _record_summary_log(
            db_session,
            status_value=status_value,
            result_code="automatic_sync_completed",
            message=message,
            payload={
                "provider": sync_result.provider.value,
                "success_count": sync_result.success_count,
                "skipped_count": sync_result.skipped_count,
                "failure_count": sync_result.failure_count,
                "used_fallback": sync_result.used_fallback,
                "interval_minutes": integration_settings.auto_sync_interval_minutes,
            },
        )
        return InternalSyncResponse(
            provider=sync_result.provider.value,
            status=status_value.value,
            operation="automatic_sync",
            message=message,
            recalculation=recalculation,
        )
