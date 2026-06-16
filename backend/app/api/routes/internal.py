from __future__ import annotations

from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import build_auth_error
from app.models.schema import SyncProvider, SyncStatus
from app.repositories.queries import get_db_session
from app.services.automatic_sync import AutomaticSyncExecution, run_automatic_sync
from app.services.recalculation_service import RecalculationSummary

router = APIRouter(prefix="/api/internal", tags=["internal"])


class InternalSyncResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    status: str
    operation: str
    message: str
    recalculation: RecalculationSummary | None = None


def _get_bearer_token(value: str | None) -> str | None:
    if value is None:
        return None
    prefix = "Bearer "
    if not value.startswith(prefix):
        return None
    token = value[len(prefix):].strip()
    return token or None


def _build_response(result: AutomaticSyncExecution) -> InternalSyncResponse:
    return InternalSyncResponse(
        provider=result.provider.value,
        status=result.status.value,
        operation=result.operation,
        message=result.message,
        recalculation=result.recalculation,
    )


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

    return _build_response(
        run_automatic_sync(
            db_session,
            trigger_source="external_trigger",
        )
    )
