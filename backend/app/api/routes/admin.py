from __future__ import annotations

import json
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

import os
_DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parents[3] / "data")))

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.schemas.frontend import (
    AdminDashboardScreenDto,
    AdminIntegrationScreenDto,
    AdminMatchesScreenDto,
    AdminPlayersScreenDto,
    AdminSettingsScreenDto,
)
from app.core.security import build_auth_error, hash_password, require_admin_user
from app.models.schema import (
    CompetitionPhase,
    CompetitionPhaseConfig,
    AccessStatus,
    CompetitionWindow,
    IntegrationSettings,
    Match,
    SyncLog,
    SyncProvider,
    SyncStatus,
    User,
    UserSession,
)
from app.repositories.queries import get_db_session, get_match_by_id
from app.services.integration_settings import integration_settings_table_exists, load_integration_settings
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


def get_or_create_integration_settings(db_session: Session) -> IntegrationSettings:
    settings_row = load_integration_settings(db_session)
    if settings_row is not None:
        return settings_row
    if not integration_settings_table_exists(db_session):
        raise build_auth_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="integration_settings_missing",
            message="integration_settings table is missing; run the database migrations",
        )
    settings_row = IntegrationSettings(
        auto_sync_enabled=False,
        auto_sync_interval_minutes=60,
    )
    db_session.add(settings_row)
    db_session.flush()
    return settings_row


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


class PlayerStatsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selection_key: str = Field(min_length=1, max_length=128)
    goals: int = Field(ge=0, le=100)
    assists: int = Field(ge=0, le=100)


class PlayerStatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selection_key: str
    goals: int
    assists: int


def _load_player_stats() -> dict[str, dict[str, int]]:
    path = _DATA_DIR / "player-stats.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_player_stats(stats: dict[str, dict[str, int]]) -> None:
    path = _DATA_DIR / "player-stats.json"
    path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


class RegisterPlayerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    team_code: str | None = Field(default=None, max_length=10)


class RegisterPlayerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    teamCode: str | None


@router.post("/players/register", response_model=RegisterPlayerResponse, status_code=status.HTTP_200_OK)
def register_player(
    payload: RegisterPlayerRequest,
    admin_user: User = Depends(require_admin_user),
) -> RegisterPlayerResponse:
    del admin_user
    from app.services.team_metadata import get_players_by_id

    name_slug = payload.name.lower().replace(" ", "-").replace(".", "")
    team_suffix = (payload.team_code or "UNK").lower()
    player_id = f"{name_slug}-{team_suffix}"

    path = _DATA_DIR / "players-attackers.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"players": []}

    existing_ids = {p.get("id") for p in data.get("players", []) if isinstance(p, dict)}
    if player_id not in existing_ids:
        data.setdefault("players", []).append({
            "id": player_id,
            "name": payload.name,
            "teamCode": payload.team_code,
            "position": "FW",
            "shirtNumber": None,
            "club": None,
            "nationality": None,
        })
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        get_players_by_id.cache_clear()

    return RegisterPlayerResponse(id=player_id, name=payload.name, teamCode=payload.team_code)


@router.put("/players/stats", response_model=PlayerStatsResponse, status_code=status.HTTP_200_OK)
def update_player_stats(
    payload: PlayerStatsRequest,
    admin_user: User = Depends(require_admin_user),
) -> PlayerStatsResponse:
    del admin_user
    stats = _load_player_stats()
    stats[payload.selection_key] = {"goals": payload.goals, "assists": payload.assists}
    _save_player_stats(stats)
    return PlayerStatsResponse(
        selection_key=payload.selection_key,
        goals=payload.goals,
        assists=payload.assists,
    )


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
    is_active: bool
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


class GoalScorerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    team: str | None = Field(default=None, max_length=100)
    goals: int = Field(default=1, ge=1, le=20)


class MatchManualOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = Field(default=None, min_length=1, max_length=32)
    official_home_goals: int | None = Field(default=None, ge=0, le=50)
    official_away_goals: int | None = Field(default=None, ge=0, le=50)
    winner_team_name: str | None = Field(default=None, min_length=1, max_length=255)
    goal_scorers: list[GoalScorerEntry] = Field(default_factory=list)
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
    include_top_scorers: bool = False
    mode: Literal["LATEST_RESULT_ONLY", "SCHEDULED"] = "LATEST_RESULT_ONLY"


class SyncRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    status: str
    operation: str
    message: str
    recalculation: RecalculationSummary | None = None


class IntegrationSettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auto_sync_enabled: bool
    auto_sync_interval_minutes: int = Field(ge=1, le=60)

    @field_validator("auto_sync_interval_minutes")
    @classmethod
    def validate_interval(cls, value: int) -> int:
        if value not in {1, 5, 15, 60}:
            raise ValueError("auto_sync_interval_minutes must be one of 1, 5, 15, 60")
        return value


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_user_response(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        access_status=user.access_status,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


@router.put("/integration/settings", response_model=AdminIntegrationScreenDto, status_code=status.HTTP_200_OK)
def update_admin_integration_settings(
    payload: IntegrationSettingsUpdateRequest,
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> AdminIntegrationScreenDto:
    settings_row = get_or_create_integration_settings(db_session)
    settings_row.auto_sync_enabled = payload.auto_sync_enabled
    settings_row.auto_sync_interval_minutes = payload.auto_sync_interval_minutes
    settings_row.updated_by_user_id = admin_user.id
    db_session.add(settings_row)
    db_session.flush()
    return FrontendContractService(db_session).build_admin_integration(integration_settings=settings_row)


@router.get("/users", response_model=list[AdminUserResponse], status_code=status.HTTP_200_OK)
def list_users(
    scope: str = Query(default="active"),
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> list[AdminUserResponse]:
    del admin_user
    statement = select(User)
    if scope == "deleted":
        statement = statement.where(User.is_active.is_(False))
    else:
        statement = statement.where(User.is_active.is_(True))
    statement = statement.order_by(User.created_at.asc(), User.id.asc())
    users = list(db_session.scalars(statement).all())
    return [build_user_response(user) for user in users]


@router.put("/users/{user_id}/moderation", response_model=AdminUserResponse, status_code=status.HTTP_200_OK)
def update_user_moderation(
    user_id: UUID,
    payload: ModerationUpdateRequest,
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> AdminUserResponse:
    user = db_session.get(User, user_id)
    if user is None:
        raise build_auth_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="user_not_found",
            message="User was not found",
        )
    if user.id == admin_user.id and payload.access_status is not AccessStatus.APPROVED:
        raise build_auth_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="cannot_demote_self",
            message="Administrator cannot change the current account to a non-approved state",
        )
    if payload.is_admin is False and user.id == admin_user.id:
        raise build_auth_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="cannot_remove_own_admin",
            message="Administrator cannot remove their own admin access",
        )
    if payload.is_admin is True and payload.access_status is not AccessStatus.APPROVED:
        raise build_auth_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="admin_must_be_approved",
            message="Administrator accounts must remain approved",
        )
    user.access_status = payload.access_status
    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    db_session.add(user)
    db_session.flush()
    return build_user_response(user)


@router.post("/users/{user_id}/soft-delete", response_model=AdminUserResponse, status_code=status.HTTP_200_OK)
def soft_delete_user(
    user_id: UUID,
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> AdminUserResponse:
    user = db_session.get(User, user_id)
    if user is None:
        raise build_auth_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="user_not_found",
            message="User was not found",
        )
    if user.id == admin_user.id:
        raise build_auth_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="cannot_delete_self",
            message="Administrator cannot delete the current account",
        )

    user.is_active = False
    user.is_admin = False
    db_session.add(user)
    db_session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=utc_now())
    )
    db_session.flush()
    return build_user_response(user)


class ResetPasswordResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    email: str
    full_name: str
    reset_at: datetime


def _generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        # require at least one digit and one letter
        if any(c.isdigit() for c in pwd) and any(c.isalpha() for c in pwd):
            return pwd


@router.post("/users/{user_id}/reset-password", response_model=ResetPasswordResponse, status_code=status.HTTP_200_OK)
def reset_user_password(
    user_id: UUID,
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> ResetPasswordResponse:
    user = db_session.get(User, user_id)
    if user is None:
        raise build_auth_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="user_not_found",
            message="User was not found",
        )
    if not user.is_active:
        raise build_auth_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="user_inactive",
            message="Inactive users cannot receive password resets",
        )
    new_password = _generate_password()
    user.password_hash = hash_password(new_password)
    db_session.add(user)
    db_session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=utc_now())
    )
    db_session.flush()
    return ResetPasswordResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        reset_at=utc_now(),
    )


@router.get("/competition/window", response_model=CompetitionWindowResponse, status_code=status.HTTP_200_OK)
def get_competition_window(
    admin_user: User = Depends(require_admin_user),
    db_session: Session = Depends(get_db_session),
) -> CompetitionWindowResponse:
    del admin_user
    phase_config = db_session.scalar(
        select(CompetitionPhaseConfig)
        .where(CompetitionPhaseConfig.is_active.is_(True))
        .order_by(CompetitionPhaseConfig.sort_order.asc(), CompetitionPhaseConfig.lock_at.asc())
    )
    if phase_config is not None:
        active_window = FrontendContractService(db_session).build_admin_settings().competitionWindow
        return CompetitionWindowResponse(
            id=phase_config.id,
            name=phase_config.phase_key,
            prediction_close_at=datetime.fromisoformat(active_window["prediction_close_at"]),
            explore_release_at=datetime.fromisoformat(active_window["explore_release_at"]),
            is_active=phase_config.is_active,
        )
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
        match.status = "FT" if payload.status == "FINISHED" else payload.status
    if payload.official_home_goals is not None:
        match.official_home_goals = payload.official_home_goals
    if payload.official_away_goals is not None:
        match.official_away_goals = payload.official_away_goals
    if payload.winner_team_name is not None:
        match.winner_team_name = payload.winner_team_name.strip()
    merged_payload = dict(payload.source_payload or {})
    if payload.goal_scorers:
        merged_payload["goal_scorers"] = [gs.model_dump() for gs in payload.goal_scorers]
    match.source_payload = merged_payload if merged_payload else match.source_payload
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
    requested_provider = payload.provider or SyncProvider.THE_SPORTS_DB
    include_top_scorers = (
        False if requested_provider is SyncProvider.THE_SPORTS_DB else payload.include_top_scorers
    )
    if payload.fixture_id is not None:
        sync_result = service.run_manual_match_sync(
            db_session,
            fixture_id=payload.fixture_id,
            created_by_user_id=admin_user.id,
            requested_provider=requested_provider,
            allow_google_sheets_fallback=payload.allow_google_sheets_fallback,
            include_top_scorers=include_top_scorers,
            recalculation_hook=recalculate_from_sync_request,
        )
        operation = "manual_match_sync"
    elif payload.mode == "LATEST_RESULT_ONLY":
        sync_result = service.run_latest_result_sync(
            db_session,
            created_by_user_id=admin_user.id,
            requested_provider=requested_provider,
            allow_google_sheets_fallback=payload.allow_google_sheets_fallback,
            include_top_scorers=include_top_scorers,
            recalculation_hook=recalculate_from_sync_request,
        )
        operation = "manual_latest_result_sync"
    else:
        sync_result = service.run_scheduled_sync(
            db_session,
            created_by_user_id=admin_user.id,
            requested_provider=requested_provider,
            allow_google_sheets_fallback=payload.allow_google_sheets_fallback,
            include_top_scorers=include_top_scorers,
            recalculation_hook=recalculate_from_sync_request,
            respect_timing_window=False,
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

_ROUND_KEYS = ["initial_predictions", "round1", "round2", "round3", "roundOf32", "roundOf16", "quarterFinal", "semiFinal", "final"]


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
    phase_config = db_session.scalar(
        select(CompetitionPhaseConfig).where(CompetitionPhaseConfig.phase_key == payload.roundKey)
    )
    if phase_config is not None:
        phase_config.is_force_locked = payload.locked
        db_session.add(phase_config)
        db_session.flush()

        current = 0
        ordered_phase_configs = list(
            db_session.scalars(
                select(CompetitionPhaseConfig)
                .where(CompetitionPhaseConfig.is_active.is_(True))
                .order_by(CompetitionPhaseConfig.sort_order.asc(), CompetitionPhaseConfig.lock_at.asc())
            ).all()
        )
        for idx, item in enumerate(ordered_phase_configs):
            if item.is_force_locked:
                current |= 1 << idx

        return PhaseLockResponse(roundKey=payload.roundKey, locked=payload.locked, forceLockedPhases=current)

    legacy_window = db_session.scalar(
        select(CompetitionWindow).where(CompetitionWindow.is_active.is_(True)).order_by(CompetitionWindow.updated_at.desc())
    )
    if legacy_window is None:
        raise build_auth_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="competition_phase_not_found",
            message="Competition phase was not found",
        )
    idx = _ROUND_KEYS.index(payload.roundKey)
    bit = 1 << idx
    current = legacy_window.force_locked_phases or 0
    if payload.locked:
        current = current | bit
    else:
        current = current & ~bit
    legacy_window.force_locked_phases = current
    db_session.add(legacy_window)
    db_session.flush()
    return PhaseLockResponse(roundKey=payload.roundKey, locked=payload.locked, forceLockedPhases=current)
