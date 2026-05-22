from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260521_0001"
down_revision = None
branch_labels = None
depends_on = None


access_status_enum = postgresql.ENUM(
    "PENDING",
    "APPROVED",
    "REJECTED",
    "BLOCKED",
    name="access_status_enum",
    create_type=False,
)
competition_phase_enum = postgresql.ENUM(
    "GROUP_STAGE",
    "ROUND_OF_32",
    "ROUND_OF_16",
    "QUARTER_FINAL",
    "SEMI_FINAL",
    "THIRD_PLACE",
    "FINAL",
    name="competition_phase_enum",
    create_type=False,
)
competition_prediction_type_enum = postgresql.ENUM(
    "CHAMPION",
    "TOP_SCORER",
    name="competition_prediction_type_enum",
    create_type=False,
)
sync_provider_enum = postgresql.ENUM(
    "API_FOOTBALL",
    "GOOGLE_SHEETS",
    "ADMIN",
    "SEED",
    name="sync_provider_enum",
    create_type=False,
)
sync_log_provider_enum = postgresql.ENUM(
    "API_FOOTBALL",
    "GOOGLE_SHEETS",
    "ADMIN",
    "SEED",
    name="sync_log_provider_enum",
    create_type=False,
)
sync_log_status_enum = postgresql.ENUM(
    "SUCCESS",
    "FAILURE",
    "SKIPPED",
    name="sync_log_status_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    access_status_enum.create(bind, checkfirst=True)
    competition_phase_enum.create(bind, checkfirst=True)
    competition_prediction_type_enum.create(bind, checkfirst=True)
    sync_provider_enum.create(bind, checkfirst=True)
    sync_log_provider_enum.create(bind, checkfirst=True)
    sync_log_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("access_status", access_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_access_status", "users", ["access_status"], unique=False)

    op.create_table(
        "competition_windows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("prediction_close_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("explore_release_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_competition_windows_is_active", "competition_windows", ["is_active"], unique=False)

    op.create_table(
        "matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_provider", sync_provider_enum, nullable=True),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("phase", competition_phase_enum, nullable=False),
        sa.Column("stage_round", sa.Integer(), nullable=True),
        sa.Column("group_name", sa.String(length=16), nullable=True),
        sa.Column("bracket_slot", sa.String(length=16), nullable=True),
        sa.Column("feeder_home_key", sa.String(length=32), nullable=True),
        sa.Column("feeder_away_key", sa.String(length=32), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("venue", sa.String(length=255), nullable=True),
        sa.Column("home_team_name", sa.String(length=255), nullable=False),
        sa.Column("away_team_name", sa.String(length=255), nullable=False),
        sa.Column("home_team_fifa_code", sa.String(length=8), nullable=True),
        sa.Column("away_team_fifa_code", sa.String(length=8), nullable=True),
        sa.Column("involves_brazil", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="SCHEDULED"),
        sa.Column("official_home_goals", sa.Integer(), nullable=True),
        sa.Column("official_away_goals", sa.Integer(), nullable=True),
        sa.Column("winner_team_name", sa.String(length=255), nullable=True),
        sa.Column("has_manual_override", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source_payload", sa.JSON(), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_provider", "external_id", name="uq_matches_provider_external_id"),
    )
    op.create_index("ix_matches_external_id", "matches", ["external_id"], unique=False)
    op.create_index("ix_matches_phase", "matches", ["phase"], unique=False)
    op.create_index("ix_matches_group_name", "matches", ["group_name"], unique=False)
    op.create_index("ix_matches_bracket_slot", "matches", ["bracket_slot"], unique=False)
    op.create_index("ix_matches_starts_at", "matches", ["starts_at"], unique=False)
    op.create_index("ix_matches_status", "matches", ["status"], unique=False)
    op.create_index("ix_matches_has_manual_override", "matches", ["has_manual_override"], unique=False)

    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"], unique=False)
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True)
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"], unique=False)

    op.create_table(
        "match_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("home_goals", sa.Integer(), nullable=False),
        sa.Column("away_goals", sa.Integer(), nullable=False),
        sa.Column("points_awarded", sa.Integer(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "match_id", name="uq_match_predictions_user_match"),
    )
    op.create_index("ix_match_predictions_user_id", "match_predictions", ["user_id"], unique=False)
    op.create_index("ix_match_predictions_match_id", "match_predictions", ["match_id"], unique=False)

    op.create_table(
        "competition_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prediction_type", competition_prediction_type_enum, nullable=False),
        sa.Column("selection_key", sa.String(length=128), nullable=False),
        sa.Column("selection_label", sa.String(length=255), nullable=False),
        sa.Column("points_awarded", sa.Integer(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "prediction_type", name="uq_competition_predictions_user_type"),
    )
    op.create_index("ix_competition_predictions_user_id", "competition_predictions", ["user_id"], unique=False)
    op.create_index("ix_competition_predictions_prediction_type", "competition_predictions", ["prediction_type"], unique=False)

    op.create_table(
        "sync_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sync_log_provider_enum, nullable=False),
        sa.Column("status", sync_log_status_enum, nullable=False),
        sa.Column("operation", sa.String(length=100), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result_code", sa.String(length=100), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_logs_provider", "sync_logs", ["provider"], unique=False)
    op.create_index("ix_sync_logs_status", "sync_logs", ["status"], unique=False)
    op.create_index("ix_sync_logs_created_by_user_id", "sync_logs", ["created_by_user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_sync_logs_created_by_user_id", table_name="sync_logs")
    op.drop_index("ix_sync_logs_status", table_name="sync_logs")
    op.drop_index("ix_sync_logs_provider", table_name="sync_logs")
    op.drop_table("sync_logs")

    op.drop_index("ix_competition_predictions_prediction_type", table_name="competition_predictions")
    op.drop_index("ix_competition_predictions_user_id", table_name="competition_predictions")
    op.drop_table("competition_predictions")

    op.drop_index("ix_match_predictions_match_id", table_name="match_predictions")
    op.drop_index("ix_match_predictions_user_id", table_name="match_predictions")
    op.drop_table("match_predictions")

    op.drop_index("ix_user_sessions_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_token_hash", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_index("ix_matches_has_manual_override", table_name="matches")
    op.drop_index("ix_matches_status", table_name="matches")
    op.drop_index("ix_matches_starts_at", table_name="matches")
    op.drop_index("ix_matches_bracket_slot", table_name="matches")
    op.drop_index("ix_matches_group_name", table_name="matches")
    op.drop_index("ix_matches_phase", table_name="matches")
    op.drop_index("ix_matches_external_id", table_name="matches")
    op.drop_table("matches")

    op.drop_index("ix_competition_windows_is_active", table_name="competition_windows")
    op.drop_table("competition_windows")

    op.drop_index("ix_users_access_status", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    sync_log_status_enum.drop(bind, checkfirst=True)
    sync_log_provider_enum.drop(bind, checkfirst=True)
    sync_provider_enum.drop(bind, checkfirst=True)
    competition_prediction_type_enum.drop(bind, checkfirst=True)
    competition_phase_enum.drop(bind, checkfirst=True)
    access_status_enum.drop(bind, checkfirst=True)
