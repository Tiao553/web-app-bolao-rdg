from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, hash_password
from app.main import create_app
from app.models.schema import (
    AccessStatus,
    Base,
    CompetitionWindow,
    IntegrationSettings,
    SyncLog,
    SyncProvider,
    SyncStatus,
    User,
)
from app.repositories.queries import get_db_session
from app.services.automatic_sync import AutomaticSyncExecution
from app.services.recalculation_service import (
    RecalculationStageSummary,
    RecalculationSummary,
)
from app.services.sync_service import SyncRunResult


def configure_test_settings() -> None:
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
    os.environ["SESSION_COOKIE_DOMAIN"] = ""
    os.environ["SYNC_ADMIN_TOKEN"] = "secret-token"
    get_settings.cache_clear()


def make_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def db_override(factory: sessionmaker[Session]) -> Iterator[Session]:
    db_session = factory()
    try:
        yield db_session
        db_session.commit()
    finally:
        db_session.close()


def build_db_override(factory: sessionmaker[Session]) -> Callable[[], Iterator[Session]]:
    def override() -> Iterator[Session]:
        yield from db_override(factory)

    return override


def issue_csrf_headers(client: TestClient) -> dict[str, str]:
    client.get("/healthz")
    csrf_token = client.cookies.get(CSRF_COOKIE_NAME)
    assert csrf_token is not None
    return {CSRF_HEADER_NAME: csrf_token}


def create_user(
    db_session: Session,
    *,
    email: str,
    status: AccessStatus,
    is_admin: bool = False,
) -> User:
    user = User(
        id=uuid4(),
        email=email,
        full_name=email.split("@")[0],
        password_hash=hash_password("password123"),
        access_status=status,
        is_admin=is_admin,
    )
    db_session.add(user)
    db_session.flush()
    return user


def seed_window(db_session: Session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add(
        CompetitionWindow(
            name="default",
            prediction_close_at=now + timedelta(hours=1),
            explore_release_at=now + timedelta(hours=2),
            is_active=True,
        )
    )
    db_session.flush()


def fake_recalculation_summary() -> RecalculationSummary:
    stage = RecalculationStageSummary(status="ok", updated_count=0, skipped_count=0, notes=None)
    return RecalculationSummary(
        executed_at=datetime.now(timezone.utc),
        standings=stage,
        bracket=stage,
        match_points=stage,
        competition_points=stage,
        ranking=stage,
        ranking_rows=[],
    )


def test_admin_can_update_integration_settings() -> None:
    configure_test_settings()
    factory = make_session_factory()
    with factory() as db_session:
        create_user(db_session, email="admin@example.com", status=AccessStatus.APPROVED, is_admin=True)
        seed_window(db_session)
        db_session.commit()

    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        headers = issue_csrf_headers(client)
        login_response = client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "password123"},
            headers=headers,
        )
        assert login_response.status_code == 200

        response = client.put(
            "/api/admin/integration/settings",
            json={"auto_sync_enabled": True, "auto_sync_interval_minutes": 15},
            headers=headers,
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["autoSyncEnabled"] is True
    assert payload["autoSyncIntervalMinutes"] == 15
    with factory() as db_session:
        row = db_session.scalar(select(IntegrationSettings))
        assert row is not None
        assert row.auto_sync_enabled is True
        assert row.auto_sync_interval_minutes == 15


def test_admin_integration_page_handles_missing_integration_settings_table() -> None:
    configure_test_settings()
    factory = make_session_factory()
    with factory() as db_session:
        create_user(db_session, email="admin@example.com", status=AccessStatus.APPROVED, is_admin=True)
        seed_window(db_session)
        db_session.commit()
        IntegrationSettings.__table__.drop(db_session.get_bind())
        db_session.commit()

    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        headers = issue_csrf_headers(client)
        login_response = client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "password123"},
            headers=headers,
        )
        assert login_response.status_code == 200

        response = client.get("/api/admin/integration")

    assert response.status_code == 200
    payload = response.json()
    assert payload["autoSyncEnabled"] is False
    assert payload["autoSyncIntervalMinutes"] == 60
    assert payload["autoSyncStatus"] == "disabled"


def test_internal_auto_sync_skips_when_disabled() -> None:
    configure_test_settings()
    factory = make_session_factory()
    with factory() as db_session:
        seed_window(db_session)
        db_session.commit()

    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        response = client.post(
            "/api/internal/sync/auto",
            headers={"Authorization": "Bearer secret-token"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "SKIPPED"


def test_internal_auto_sync_rejects_invalid_token() -> None:
    configure_test_settings()
    factory = make_session_factory()
    with factory() as db_session:
        seed_window(db_session)
        db_session.commit()

    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        response = client.post(
            "/api/internal/sync/auto",
            headers={"Authorization": "Bearer wrong-token"},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_sync_token"


def test_internal_auto_sync_requires_configured_token() -> None:
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
    os.environ["SESSION_COOKIE_DOMAIN"] = ""
    os.environ["SYNC_ADMIN_TOKEN"] = ""
    get_settings.cache_clear()

    factory = make_session_factory()
    with factory() as db_session:
        seed_window(db_session)
        db_session.commit()

    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        response = client.post(
            "/api/internal/sync/auto",
            headers={"Authorization": "Bearer anything"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "sync_admin_token_missing"


def test_internal_auto_sync_runs_when_due(monkeypatch) -> None:
    configure_test_settings()
    factory = make_session_factory()
    with factory() as db_session:
        seed_window(db_session)
        db_session.add(IntegrationSettings(auto_sync_enabled=True, auto_sync_interval_minutes=1))
        db_session.commit()

    monkeypatch.setattr(
        "app.api.routes.internal.run_automatic_sync",
        lambda db_session, *, trigger_source: AutomaticSyncExecution(
            provider=SyncProvider.THE_SPORTS_DB,
            status=SyncStatus.SUCCESS,
            operation="automatic_sync",
            message="Automatic sync completed with 0 success(es), 0 skip(s), and 0 failure(s)",
            recalculation=fake_recalculation_summary(),
        ),
    )

    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        response = client.post(
            "/api/internal/sync/auto",
            headers={"Authorization": "Bearer secret-token"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "THE_SPORTS_DB"
    assert payload["operation"] == "automatic_sync"
    assert payload["status"] == "SUCCESS"


def test_internal_auto_sync_skips_when_not_due() -> None:
    configure_test_settings()
    factory = make_session_factory()
    with factory() as db_session:
        seed_window(db_session)
        db_session.add(IntegrationSettings(auto_sync_enabled=True, auto_sync_interval_minutes=15))
        db_session.add(
            SyncLog(
                provider=SyncProvider.THE_SPORTS_DB,
                status=SyncStatus.SUCCESS,
                operation="automatic_sync",
                match_id=None,
                created_by_user_id=None,
                result_code="automatic_sync_completed",
                message="recent run",
                payload={},
            )
        )
        db_session.commit()

    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        response = client.post(
            "/api/internal/sync/auto",
            headers={"Authorization": "Bearer secret-token"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "SKIPPED"
    assert payload["message"].startswith("Automatic sync is not due until ")
