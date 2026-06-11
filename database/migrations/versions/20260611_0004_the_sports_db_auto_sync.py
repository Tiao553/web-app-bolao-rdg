"""add the sports db provider and integration settings

Revision ID: 20260611_0004
Revises: 20260606_0003
Create Date: 2026-06-11

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260611_0004"
down_revision = "20260606_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE sync_provider_enum ADD VALUE IF NOT EXISTS 'THE_SPORTS_DB'")
    op.execute("ALTER TYPE sync_log_provider_enum ADD VALUE IF NOT EXISTS 'THE_SPORTS_DB'")

    op.create_table(
        "integration_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("auto_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("auto_sync_interval_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_integration_settings_updated_by_user_id", "integration_settings", ["updated_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_integration_settings_updated_by_user_id", table_name="integration_settings")
    op.drop_table("integration_settings")
