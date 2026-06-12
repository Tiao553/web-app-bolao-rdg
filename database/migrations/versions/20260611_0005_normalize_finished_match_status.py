"""normalize finished match statuses to FT

Revision ID: 20260611_0005
Revises: 20260611_0004
Create Date: 2026-06-11

"""
from __future__ import annotations

from alembic import op

revision = "20260611_0005"
down_revision = "20260611_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE matches SET status = 'FT' WHERE status = 'FINISHED'")


def downgrade() -> None:
    op.execute("UPDATE matches SET status = 'FINISHED' WHERE status = 'FT'")

