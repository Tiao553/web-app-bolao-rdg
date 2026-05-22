from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, joinedload, sessionmaker
from sqlalchemy.sql import Select

from app.core.config import Settings, get_settings
from app.models.schema import (
    AccessStatus,
    CompetitionPrediction,
    CompetitionWindow,
    Match,
    MatchPrediction,
    PredictionType,
    User,
    UserSession,
)


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://") and "+" not in database_url.split("://", 1)[0]:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url

_engine: Engine | None = None
_session_local: sessionmaker[Session] | None = None


def get_runtime_settings() -> Settings:
    return get_settings()


@dataclass(frozen=True, slots=True)
class CompetitionWindowSnapshot:
    prediction_close_at: datetime
    explore_release_at: datetime


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
    return select(User).where(User.access_status == AccessStatus.APPROVED)


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
    if db_user_session.user.access_status is AccessStatus.BLOCKED:
        return None
    return db_user_session


def get_active_competition_window(db_session: Session) -> CompetitionWindowSnapshot:
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
        .where(User.access_status == AccessStatus.APPROVED)
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
        .where(User.access_status == AccessStatus.APPROVED)
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
        .where(User.access_status == AccessStatus.APPROVED)
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
