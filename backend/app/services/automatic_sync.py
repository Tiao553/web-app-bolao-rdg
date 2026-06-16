from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from app.models.schema import IntegrationSettings, SyncLog, SyncProvider, SyncStatus
from app.services.integration_settings import load_integration_settings
from app.services.recalculation_service import (
    RecalculationSummary,
    recalculate_competition_state,
    recalculate_from_sync_request,
)
from app.services.sync_service import SyncService, resolve_sync_log_provider

AUTO_SYNC_LOCK_KEY = 2026061101
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AutomaticSyncExecution:
    provider: SyncProvider
    status: SyncStatus
    operation: str
    message: str
    recalculation: RecalculationSummary | None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def latest_auto_sync_log(db_session: Session) -> SyncLog | None:
    return db_session.scalar(
        select(SyncLog)
        .where(SyncLog.operation == "automatic_sync")
        .order_by(SyncLog.created_at.desc(), SyncLog.id.desc())
    )


@contextmanager
def advisory_lock(db_session: Session) -> Iterator[bool]:
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


def record_summary_log(
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


def run_automatic_sync(
    db_session: Session,
    *,
    sync_service: SyncService | None = None,
    now_provider: Callable[[], datetime] | None = None,
    trigger_source: str = "runtime_worker",
) -> AutomaticSyncExecution:
    integration_settings = load_integration_settings(db_session)
    if integration_settings is None or not integration_settings.auto_sync_enabled:
        return AutomaticSyncExecution(
            provider=SyncProvider.THE_SPORTS_DB,
            status=SyncStatus.SKIPPED,
            operation="automatic_sync",
            message="Automatic sync is disabled",
            recalculation=None,
        )

    current_time = now_provider() if now_provider is not None else utc_now()
    last_log = latest_auto_sync_log(db_session)
    if last_log is not None:
        next_due_at = as_utc(last_log.created_at) + timedelta(
            minutes=integration_settings.auto_sync_interval_minutes
        )
        if next_due_at > current_time:
            return AutomaticSyncExecution(
                provider=SyncProvider.THE_SPORTS_DB,
                status=SyncStatus.SKIPPED,
                operation="automatic_sync",
                message=f"Automatic sync is not due until {next_due_at.isoformat()}",
                recalculation=None,
            )

    service = sync_service or SyncService()
    with advisory_lock(db_session) as acquired:
        if not acquired:
            return AutomaticSyncExecution(
                provider=SyncProvider.THE_SPORTS_DB,
                status=SyncStatus.SKIPPED,
                operation="automatic_sync",
                message="Another automatic sync is already running",
                recalculation=None,
            )

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
            record_summary_log(
                db_session,
                status_value=SyncStatus.FAILURE,
                result_code="automatic_sync_failed",
                message=str(exc),
                payload={
                    "provider": SyncProvider.THE_SPORTS_DB.value,
                    "interval_minutes": integration_settings.auto_sync_interval_minutes,
                    "trigger_source": trigger_source,
                },
            )
            db_session.commit()
            raise

        status_value = (
            SyncStatus.SUCCESS
            if sync_result.failure_count == 0
            else SyncStatus.FAILURE
        )
        message = (
            f"Automatic sync completed with {sync_result.success_count} success(es), "
            f"{sync_result.skipped_count} skip(s), and {sync_result.failure_count} failure(s)"
        )
        record_summary_log(
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
                "trigger_source": trigger_source,
            },
        )
        return AutomaticSyncExecution(
            provider=sync_result.provider,
            status=status_value,
            operation="automatic_sync",
            message=message,
            recalculation=recalculation,
        )


class AutoSyncWorker:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        poll_seconds: int,
        trigger_source: str = "runtime_worker",
    ) -> None:
        self._session_factory = session_factory
        self._poll_seconds = poll_seconds
        self._trigger_source = trigger_source
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(
            self._run_loop(),
            name="automatic-sync-worker",
        )

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    async def run_once(self) -> None:
        await asyncio.to_thread(self._run_once_blocking)

    async def _run_loop(self) -> None:
        while True:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.exception("automatic sync worker tick failed")
            await asyncio.sleep(self._poll_seconds)

    def _run_once_blocking(self) -> None:
        db_session = self._session_factory()
        try:
            run_automatic_sync(
                db_session,
                trigger_source=self._trigger_source,
            )
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
        finally:
            db_session.close()
