from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, joinedload, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import Select

from app.core.config import Settings, get_settings
from app.models.schema import (
    AccessStatus,
    CompetitionPrediction,
    CompetitionPhaseConfig,
    CompetitionWindow,
    Match,
    MatchPrediction,
    PredictionType,
    ScoringRule,
    User,
    UserSession,
)


def normalize_database_url(database_url: str) -> str:
    database_url = database_url.strip().strip("'\"")
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://") and "+" not in database_url.split("://", 1)[0]:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def build_connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {
        "connect_timeout": 10,
        # Disable server-side prepared statements for transaction-pooled Postgres
        # connections to avoid intermittent DuplicatePreparedStatement failures.
        "prepare_threshold": None,
    }

_engine: Engine | None = None
_session_local: sessionmaker[Session] | None = None


def get_runtime_settings() -> Settings:
    return get_settings()


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class CompetitionWindowSnapshot:
    prediction_close_at: datetime
    explore_release_at: datetime


@dataclass(frozen=True, slots=True)
class CompetitionPhaseConfigSnapshot:
    id: UUID
    phase_key: str
    label: str
    phase: str | None
    stage_round: int | None
    sort_order: int
    first_match_starts_at: datetime | None
    lock_at: datetime
    explore_at: datetime
    is_force_locked: bool
    is_active: bool


@dataclass(frozen=True, slots=True)
class ScoringRuleSnapshot:
    id: UUID
    name: str
    exact_points: int
    result_points: int
    brazil_multiplier: int
    champion_points: int
    top_scorer_points: int
    is_active: bool


def get_db_session() -> Iterator[Session]:
    db_session = get_session_local()()
    try:
        yield db_session
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
    finally:
        db_session.close()


DB_SESSION_DEPENDENCY = Depends(get_db_session)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_runtime_settings()
        _engine = create_engine(
            normalize_database_url(settings.database_url),
            connect_args=build_connect_args(settings.database_url),
            poolclass=NullPool,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


def get_session_local() -> sessionmaker[Session]:
    global _session_local
    if _session_local is None:
        _session_local = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )
    return _session_local


def get_user_by_id(db_session: Session, user_id: UUID) -> User | None:
    statement = select(User).where(User.id == user_id)
    return db_session.scalar(statement)


def get_user_by_email(db_session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email.strip().lower())
    return db_session.scalar(statement)


def approved_users_select() -> Select[tuple[User]]:
    return select(User).where(
        User.access_status == AccessStatus.APPROVED,
        User.is_active.is_(True),
    )


def list_approved_users(db_session: Session) -> list[User]:
    statement = approved_users_select().order_by(User.created_at.asc())
    return list(db_session.scalars(statement).all())


def get_active_db_session_by_token_hash(
    db_session: Session,
    token_hash: str,
) -> UserSession | None:
    now = datetime.now(timezone.utc)
    statement = (
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(
            UserSession.token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
    )
    db_user_session = db_session.scalar(statement)
    if db_user_session is None:
        return None
    if not db_user_session.user.is_active or db_user_session.user.access_status is AccessStatus.BLOCKED:
        return None
    return db_user_session


def get_active_competition_window(db_session: Session) -> CompetitionWindowSnapshot:
    now = datetime.now(timezone.utc)
    phase_configs = list_active_competition_phase_configs(db_session)
    if phase_configs:
        ordered = sorted(phase_configs, key=lambda item: (item.sort_order, item.lock_at, item.phase_key))
        explore_release_at = ordered[0].explore_at
        future_deadlines = [
            cfg.lock_at
            for cfg in ordered
            if cfg.phase_key != "initial_predictions" and as_utc(cfg.lock_at) > now
        ]
        if future_deadlines:
            prediction_close_at = min(future_deadlines)
        else:
            prediction_candidates = [cfg.lock_at for cfg in ordered if cfg.phase_key != "initial_predictions"] or [ordered[-1].lock_at]
            prediction_close_at = max(prediction_candidates)
        return CompetitionWindowSnapshot(
            prediction_close_at=prediction_close_at,
            explore_release_at=explore_release_at,
        )

    statement = (
        select(CompetitionWindow)
        .where(CompetitionWindow.is_active.is_(True))
        .order_by(CompetitionWindow.updated_at.desc())
    )
    competition_window = db_session.scalar(statement)
    if competition_window is None:
        settings = get_runtime_settings()
        return CompetitionWindowSnapshot(
            prediction_close_at=settings.competition.prediction_close_at,
            explore_release_at=settings.competition.explore_release_at,
        )
    return CompetitionWindowSnapshot(
        prediction_close_at=competition_window.prediction_close_at,
        explore_release_at=competition_window.explore_release_at,
    )


def list_active_competition_phase_configs(db_session: Session) -> list[CompetitionPhaseConfigSnapshot]:
    statement = (
        select(CompetitionPhaseConfig)
        .where(CompetitionPhaseConfig.is_active.is_(True))
        .order_by(CompetitionPhaseConfig.sort_order.asc(), CompetitionPhaseConfig.lock_at.asc())
    )
    rows = list(db_session.scalars(statement).all())
    return [
        CompetitionPhaseConfigSnapshot(
            id=row.id,
            phase_key=row.phase_key,
            label=row.label,
            phase=row.phase.value if row.phase is not None else None,
            stage_round=row.stage_round,
            sort_order=row.sort_order,
            first_match_starts_at=as_utc(row.first_match_starts_at) if row.first_match_starts_at is not None else None,
            lock_at=as_utc(row.lock_at),
            explore_at=as_utc(row.explore_at),
            is_force_locked=row.is_force_locked,
            is_active=row.is_active,
        )
        for row in rows
    ]


def get_active_scoring_rule(db_session: Session) -> ScoringRuleSnapshot:
    statement = (
        select(ScoringRule)
        .where(ScoringRule.is_active.is_(True))
        .order_by(ScoringRule.updated_at.desc(), ScoringRule.created_at.desc())
    )
    scoring_rule = db_session.scalar(statement)
    if scoring_rule is None:
        settings = get_runtime_settings()
        scoring = settings.scoring
        return ScoringRuleSnapshot(
            id=UUID(int=0),
            name="default",
            exact_points=scoring.exact_points,
            result_points=scoring.result_points,
            brazil_multiplier=scoring.brazil_multiplier,
            champion_points=scoring.champion_points,
            top_scorer_points=scoring.top_scorer_points,
            is_active=True,
        )
    return ScoringRuleSnapshot(
        id=scoring_rule.id,
        name=scoring_rule.name,
        exact_points=scoring_rule.exact_points,
        result_points=scoring_rule.result_points,
        brazil_multiplier=scoring_rule.brazil_multiplier,
        champion_points=scoring_rule.champion_points,
        top_scorer_points=scoring_rule.top_scorer_points,
        is_active=scoring_rule.is_active,
    )


def get_match_by_id(db_session: Session, match_id: UUID) -> Match | None:
    statement = select(Match).where(Match.id == match_id)
    return db_session.scalar(statement)


def get_match_prediction(
    db_session: Session,
    *,
    user_id: UUID,
    match_id: UUID,
) -> MatchPrediction | None:
    statement = select(MatchPrediction).where(
        MatchPrediction.user_id == user_id,
        MatchPrediction.match_id == match_id,
    )
    return db_session.scalar(statement)


def get_competition_prediction(
    db_session: Session,
    *,
    user_id: UUID,
    prediction_type: PredictionType,
) -> CompetitionPrediction | None:
    statement = select(CompetitionPrediction).where(
        CompetitionPrediction.user_id == user_id,
        CompetitionPrediction.prediction_type == prediction_type,
    )
    return db_session.scalar(statement)


def ranking_users_select() -> Select[tuple[User]]:
    return (
        select(User)
        .where(User.access_status == AccessStatus.APPROVED, User.is_active.is_(True))
        .order_by(User.created_at.asc(), User.id.asc())
    )


def visible_match_predictions_select(
    *,
    viewer: User,
    explore_released: bool,
) -> Select[tuple[MatchPrediction]]:
    statement = (
        select(MatchPrediction)
        .join(User, User.id == MatchPrediction.user_id)
        .options(
            joinedload(MatchPrediction.user),
            joinedload(MatchPrediction.match),
        )
        .where(User.access_status == AccessStatus.APPROVED, User.is_active.is_(True))
        .order_by(MatchPrediction.created_at.asc(), MatchPrediction.id.asc())
    )
    if not explore_released or viewer.access_status is not AccessStatus.APPROVED:
        statement = statement.where(MatchPrediction.user_id == viewer.id)
    return statement


def visible_competition_predictions_select(
    *,
    viewer: User,
    explore_released: bool,
) -> Select[tuple[CompetitionPrediction]]:
    statement = (
        select(CompetitionPrediction)
        .join(User, User.id == CompetitionPrediction.user_id)
        .options(joinedload(CompetitionPrediction.user))
        .where(User.access_status == AccessStatus.APPROVED, User.is_active.is_(True))
        .order_by(
            CompetitionPrediction.created_at.asc(),
            CompetitionPrediction.id.asc(),
        )
    )
    if not explore_released or viewer.access_status is not AccessStatus.APPROVED:
        statement = statement.where(CompetitionPrediction.user_id == viewer.id)
    return statement


def get_competition_window_dependency(
    db_session: Session = DB_SESSION_DEPENDENCY,
) -> CompetitionWindowSnapshot:
    return get_active_competition_window(db_session)
