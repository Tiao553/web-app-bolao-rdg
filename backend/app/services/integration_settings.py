from __future__ import annotations

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.models.schema import IntegrationSettings


def integration_settings_table_exists(db_session: Session) -> bool:
    bind = db_session.bind
    if bind is None:
        return False
    try:
        return inspect(bind).has_table(IntegrationSettings.__tablename__)
    except Exception:
        return False


def load_integration_settings(db_session: Session) -> IntegrationSettings | None:
    if not integration_settings_table_exists(db_session):
        return None
    return db_session.scalar(
        select(IntegrationSettings).order_by(IntegrationSettings.updated_at.desc(), IntegrationSettings.id.desc())
    )

