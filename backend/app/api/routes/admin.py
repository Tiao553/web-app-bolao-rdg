from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.frontend import (
    AdminDashboardScreenDto,
    AdminIntegrationScreenDto,
    AdminMatchesScreenDto,
    AdminPlayersScreenDto,
    AdminSettingsScreenDto,
)
from app.core.security import build_auth_error, require_admin_user
from app.models.schema import (
    CompetitionPhase,
    AccessStatus,
    CompetitionWindow,
    Match,
    SyncLog,
    SyncProvider,
    SyncStatus,
    User,
)
from app.repositories.queries import get_db_session, get_match_by_id
from app.services.frontend_contract_service import FrontendContractService
from app.services.recalculation_service import (
    RecalculationSummary,
    recalculate_competition_state,
    recalculate_for_match,
    recalculate_from_sync_request,
)
from app.services.sync_service import SyncService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardScreenDto, status_code=status.HTTP_200_OK)
def get_admin_dashboard(
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> AdminDashboardScreenDto:
    del admin_user
    return FrontendContractService(db_session).build_admin_dashboard()


@router.get("/integration", response_model=AdminIntegrationScreenDto, status_code=status.HTTP_200_OK)
def get_admin_integration(
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> AdminIntegrationScreenDto:
    del admin_user
    return FrontendContractService(db_session).build_admin_integration()


@router.get("/matches", response_model=AdminMatchesScreenDto, status_code=status.HTTP_200_OK)
def get_admin_matches(
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> AdminMatchesScreenDto:
    del admin_user
    return FrontendContractService(db_session).build_admin_matches()


@router.get("/results", response_model=AdminMatchesScreenDto, status_code=status.HTTP_200_OK)
def get_admin_results(
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> AdminMatchesScreenDto:
    del admin_user
    return FrontendContractService(db_session).build_admin_results()


@router.get("/players", response_model=AdminPlayersScreenDto, status_code=status.HTTP_200_OK)
def get_admin_players(
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> AdminPlayersScreenDto:
    del admin_user
    return FrontendContractService(db_session).build_admin_players()


@router.get("/settings", response_model=AdminSettingsScreenDto, status_code=status.HTTP_200_OK)
def get_admin_settings(
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> AdminSettingsScreenDto:
    del admin_user
    return FrontendContractService(db_session).build_admin_settings()


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    email: str
    full_name: str
    access_status: AccessStatus
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None


class ModerationUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_status: AccessStatus
    is_admin: bool | None = None


class CompetitionWindowUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="default", min_length=1, max_length=100)
    prediction_close_at: datetime
    explore_release_at: datetime

    @field_validator("explore_release_at")
    @classmethod
    def validate_window_order(cls, value: datetime, info: Any) -> datetime:
        prediction_close_at = info.data.get("prediction_close_at")
        if isinstance(prediction_close_at, datetime) and value < prediction_close_at:
            msg = "explore_release_at must be greater than or equal to prediction_close_at"
            raise ValueError(msg)
        return value


class CompetitionWindowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    prediction_close_at: datetime
    explore_release_at: datetime
    is_active: bool


class MatchManualOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = Field(default=None, min_length=1, max_length=32)
    official_home_goals: int | None = Field(default=None, ge=0, le=50)
    official_away_goals: int | None = Field(default=None, ge=0, le=50)
    winner_team_name: str | None = Field(default=None, min_length=1, max_length=255)
    synced_at: datetime | None = None
    has_manual_override: bool = True
    source_payload: dict[str, Any] | None = None


class MatchAdminResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: str
    official_home_goals: int | None
    official_away_goals: int | None
    winner_team_name: str | None
    has_manual_override: bool
    synced_at: datetime | None


class SyncRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fixture_id: str | None = Field(default=None, min_length=1, max_length=128)
    provider: SyncProvider | None = None
    allow_google_sheets_fallback: bool = False
    include_top_scorers: bool = True


class SyncRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    status: str
    operation: str
    message: str
    recalculation: RecalculationSummary | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_user_response(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        access_status=user.access_status,
        is_admin=user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


@router.get("/users", response_model=list[AdminUserResponse], status_code=status.HTTP_200_OK)
def list_users(
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> list[AdminUserResponse]:
    del admin_user
    statement = select(User).order_by(User.created_at.asc(), User.id.asc())
    users = list(db_session.scalars(statement).all())
    return [build_user_response(user) for user in users]


@router.put("/users/{user_id}/moderation", response_model=AdminUserResponse, status_code=status.HTTP_200_OK)
def update_user_moderation(
    user_id: UUID,
    payload: ModerationUpdateRequest,
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> AdminUserResponse:
    del admin_user
    user = db_session.get(User, user_id)
    if user is None:
        raise build_auth_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="user_not_found",
            message="User was not found",
        )
    user.access_status = payload.access_status
    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    db_session.add(user)
    db_session.flush()
    return build_user_response(user)


@router.get("/competition/window", response_model=CompetitionWindowResponse, status_code=status.HTTP_200_OK)
def get_competition_window(
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> CompetitionWindowResponse:
    del admin_user
    statement = (
        select(CompetitionWindow)
        .where(CompetitionWindow.is_active.is_(True))
        .order_by(CompetitionWindow.updated_at.desc())
    )
    competition_window = db_session.scalar(statement)
    if competition_window is None:
        raise build_auth_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="competition_window_not_found",
            message="Competition window was not configured",
        )
    return CompetitionWindowResponse(
        id=competition_window.id,
        name=competition_window.name,
        prediction_close_at=competition_window.prediction_close_at,
        explore_release_at=competition_window.explore_release_at,
        is_active=competition_window.is_active,
    )


@router.put("/competition/window", response_model=CompetitionWindowResponse, status_code=status.HTTP_200_OK)
def update_competition_window(
    payload: CompetitionWindowUpdateRequest,
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> CompetitionWindowResponse:
    statement = select(CompetitionWindow).where(CompetitionWindow.name == payload.name)
    competition_window = db_session.scalar(statement)
    if competition_window is None:
        competition_window = CompetitionWindow(
            name=payload.name,
            prediction_close_at=payload.prediction_close_at,
            explore_release_at=payload.explore_release_at,
            is_active=True,
            created_by_user_id=admin_user.id,
            updated_by_user_id=admin_user.id,
        )
        db_session.add(competition_window)
    else:
        competition_window.prediction_close_at = payload.prediction_close_at
        competition_window.explore_release_at = payload.explore_release_at
        competition_window.is_active = True
        competition_window.updated_by_user_id = admin_user.id
        db_session.add(competition_window)
    deactivate_statement = select(CompetitionWindow).where(
        CompetitionWindow.name != payload.name,
        CompetitionWindow.is_active.is_(True),
    )
    active_windows = list(db_session.scalars(deactivate_statement).all())
    for active_window in active_windows:
        active_window.is_active = False
        active_window.updated_by_user_id = admin_user.id
        db_session.add(active_window)
    db_session.flush()
    return CompetitionWindowResponse(
        id=competition_window.id,
        name=competition_window.name,
        prediction_close_at=competition_window.prediction_close_at,
        explore_release_at=competition_window.explore_release_at,
        is_active=competition_window.is_active,
    )


@router.put("/matches/{match_id}/manual-override", response_model=MatchAdminResponse, status_code=status.HTTP_200_OK)
def update_match_manual_override(
    match_id: UUID,
    payload: MatchManualOverrideRequest,
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> MatchAdminResponse:
    match = get_match_by_id(db_session, match_id)
    if match is None:
        raise build_auth_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="match_not_found",
            message="Match was not found",
        )
    if payload.status is not None:
        match.status = payload.status
    if payload.official_home_goals is not None:
        match.official_home_goals = payload.official_home_goals
    if payload.official_away_goals is not None:
        match.official_away_goals = payload.official_away_goals
    if payload.winner_team_name is not None:
        match.winner_team_name = payload.winner_team_name.strip()
    if payload.source_payload is not None:
        match.source_payload = payload.source_payload
    match.has_manual_override = payload.has_manual_override
    match.synced_at = payload.synced_at or utc_now()
    db_session.add(match)
    db_session.flush()
    recalculation_summary = recalculate_for_match(db_session, match_id=match.id)
    sync_log = SyncLog(
        provider=SyncProvider.ADMIN,
        status=SyncStatus.SUCCESS,
        operation="manual_match_override",
        match_id=match.id,
        created_by_user_id=admin_user.id,
        result_code="manual_override_applied",
        message="Manual override applied and recalculation executed",
        payload=recalculation_summary.model_dump(mode="json"),
    )
    db_session.add(sync_log)
    db_session.flush()
    return MatchAdminResponse(
        id=match.id,
        status=match.status,
        official_home_goals=match.official_home_goals,
        official_away_goals=match.official_away_goals,
        winner_team_name=match.winner_team_name,
        has_manual_override=match.has_manual_override,
        synced_at=match.synced_at,
    )


@router.post("/sync/run", response_model=SyncRunResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_sync(
    payload: SyncRunRequest,
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> SyncRunResponse:
    service = SyncService()
    if payload.fixture_id is not None:
        sync_result = service.run_manual_match_sync(
            db_session,
            fixture_id=payload.fixture_id,
            created_by_user_id=admin_user.id,
            requested_provider=payload.provider,
            allow_google_sheets_fallback=payload.allow_google_sheets_fallback,
            include_top_scorers=payload.include_top_scorers,
            recalculation_hook=recalculate_from_sync_request,
        )
        operation = "manual_match_sync"
    else:
        sync_result = service.run_scheduled_sync(
            db_session,
            created_by_user_id=admin_user.id,
            requested_provider=payload.provider,
            allow_google_sheets_fallback=payload.allow_google_sheets_fallback,
            include_top_scorers=payload.include_top_scorers,
            recalculation_hook=recalculate_from_sync_request,
        )
        operation = "scheduled_sync"
    recalculation = recalculate_competition_state(db_session)
    status_value = SyncStatus.SUCCESS.value if sync_result.failure_count == 0 else SyncStatus.FAILURE.value
    message = (
        f"Sync completed with {sync_result.success_count} success(es), "
        f"{sync_result.skipped_count} skip(s), and {sync_result.failure_count} failure(s)"
    )
    return SyncRunResponse(
        provider=sync_result.provider.value,
        status=status_value,
        operation=operation,
        message=message,
        recalculation=recalculation,
    )


# ── Force phase lock / unlock ──────────────────────────────────────────────────

_ROUND_KEYS = ["round1", "round2", "round3", "roundOf32", "roundOf16", "quarterFinal", "semiFinal", "final"]


class PhaseLockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    roundKey: str
    locked: bool  # True = force lock, False = release force lock


class PhaseLockResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    roundKey: str
    locked: bool
    forceLockedPhases: int


@router.post("/phase-lock", response_model=PhaseLockResponse, status_code=status.HTTP_200_OK)
def set_phase_lock(
    payload: PhaseLockRequest,
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> PhaseLockResponse:
    if payload.roundKey not in _ROUND_KEYS:
        raise build_auth_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="invalid_round_key",
            message=f"roundKey must be one of {_ROUND_KEYS}",
        )
    idx = _ROUND_KEYS.index(payload.roundKey)
    bit = 1 << idx

    cw = db_session.scalar(select(CompetitionWindow).where(CompetitionWindow.is_active == True))  # noqa: E712
    if cw is None:
        raise build_auth_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="competition_window_not_found",
            message="No active competition window",
        )

    current = cw.force_locked_phases or 0
    if payload.locked:
        current = current | bit
    else:
        current = current & ~bit

    cw.force_locked_phases = current
    db_session.flush()

    return PhaseLockResponse(roundKey=payload.roundKey, locked=payload.locked, forceLockedPhases=current)
