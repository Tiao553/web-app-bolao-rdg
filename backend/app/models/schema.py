from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class AccessStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


class CompetitionPhase(str, Enum):
    GROUP_STAGE = "GROUP_STAGE"
    ROUND_OF_32 = "ROUND_OF_32"
    ROUND_OF_16 = "ROUND_OF_16"
    QUARTER_FINAL = "QUARTER_FINAL"
    SEMI_FINAL = "SEMI_FINAL"
    THIRD_PLACE = "THIRD_PLACE"
    FINAL = "FINAL"


class PredictionType(str, Enum):
    CHAMPION = "CHAMPION"
    TOP_SCORER = "TOP_SCORER"


class SyncProvider(str, Enum):
    API_FOOTBALL = "API_FOOTBALL"
    GOOGLE_SHEETS = "GOOGLE_SHEETS"
    ADMIN = "ADMIN"
    SEED = "SEED"


class SyncStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    access_status: Mapped[AccessStatus] = mapped_column(
        SQLEnum(AccessStatus, name="access_status_enum"),
        default=AccessStatus.PENDING,
        server_default=AccessStatus.PENDING.value,
        index=True,
        nullable=False,
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        index=True,
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    match_predictions: Mapped[list[MatchPrediction]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    competition_predictions: Mapped[list[CompetitionPrediction]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    created_sync_logs: Mapped[list[SyncLog]] = relationship(
        back_populates="created_by_user",
        foreign_keys="SyncLog.created_by_user_id",
    )


class UserSession(TimestampMixin, Base):
    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="sessions")


class CompetitionWindow(TimestampMixin, Base):
    __tablename__ = "competition_windows"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    prediction_close_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    explore_release_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        index=True,
        nullable=False,
    )
    # Bitmask: bit 0 = round1 force-locked, bit 1 = round2, bit 2 = round3, etc.
    # If bit is set, that round is locked regardless of schedule. -1 = all unlocked override.
    force_locked_phases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    updated_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class Match(TimestampMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint(
            "external_provider",
            "external_id",
            name="uq_matches_provider_external_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    external_provider: Mapped[SyncProvider | None] = mapped_column(
        SQLEnum(SyncProvider, name="sync_provider_enum"),
    )
    external_id: Mapped[str | None] = mapped_column(String(128), index=True)
    phase: Mapped[CompetitionPhase] = mapped_column(
        SQLEnum(CompetitionPhase, name="competition_phase_enum"),
        index=True,
        nullable=False,
    )
    stage_round: Mapped[int | None] = mapped_column(Integer)
    group_name: Mapped[str | None] = mapped_column(String(16), index=True)
    bracket_slot: Mapped[str | None] = mapped_column(String(16), index=True)
    feeder_home_key: Mapped[str | None] = mapped_column(String(32))
    feeder_away_key: Mapped[str | None] = mapped_column(String(32))
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )
    venue: Mapped[str | None] = mapped_column(String(255))
    home_team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    away_team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    home_team_fifa_code: Mapped[str | None] = mapped_column(String(8))
    away_team_fifa_code: Mapped[str | None] = mapped_column(String(8))
    involves_brazil: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
        server_default="SCHEDULED",
    )
    official_home_goals: Mapped[int | None] = mapped_column(Integer)
    official_away_goals: Mapped[int | None] = mapped_column(Integer)
    winner_team_name: Mapped[str | None] = mapped_column(String(255))
    has_manual_override: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        index=True,
        nullable=False,
    )
    source_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    predictions: Mapped[list[MatchPrediction]] = relationship(
        back_populates="match",
        cascade="all, delete-orphan",
    )
    sync_logs: Mapped[list[SyncLog]] = relationship(back_populates="match")


class MatchPrediction(TimestampMixin, Base):
    __tablename__ = "match_predictions"
    __table_args__ = (
        UniqueConstraint("user_id", "match_id", name="uq_match_predictions_user_match"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    match_id: Mapped[UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    home_goals: Mapped[int] = mapped_column(Integer, nullable=False)
    away_goals: Mapped[int] = mapped_column(Integer, nullable=False)
    points_awarded: Mapped[int | None] = mapped_column(Integer)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="match_predictions")
    match: Mapped[Match] = relationship(back_populates="predictions")


class CompetitionPrediction(TimestampMixin, Base):
    __tablename__ = "competition_predictions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "prediction_type",
            name="uq_competition_predictions_user_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    prediction_type: Mapped[PredictionType] = mapped_column(
        SQLEnum(PredictionType, name="competition_prediction_type_enum"),
        index=True,
        nullable=False,
    )
    selection_key: Mapped[str] = mapped_column(String(128), nullable=False)
    selection_label: Mapped[str] = mapped_column(String(255), nullable=False)
    points_awarded: Mapped[int | None] = mapped_column(Integer)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="competition_predictions")


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider: Mapped[SyncProvider] = mapped_column(
        SQLEnum(SyncProvider, name="sync_log_provider_enum"),
        index=True,
        nullable=False,
    )
    status: Mapped[SyncStatus] = mapped_column(
        SQLEnum(SyncStatus, name="sync_log_status_enum"),
        index=True,
        nullable=False,
    )
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    match_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("matches.id", ondelete="SET NULL")
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    result_code: Mapped[str | None] = mapped_column(String(100))
    message: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    match: Mapped[Match | None] = relationship(back_populates="sync_logs")
    created_by_user: Mapped[User | None] = relationship(
        back_populates="created_sync_logs",
        foreign_keys=[created_by_user_id],
    )


class PasswordResetToken(TimestampMixin, Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(backref="password_reset_tokens")
