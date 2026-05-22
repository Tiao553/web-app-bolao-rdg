from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, hash_password
from app.main import create_app
from app.models.schema import AccessStatus, Base, CompetitionWindow, User
from app.repositories.queries import get_db_session


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


def create_user(
    db_session: Session,
    *,
    email: str,
    status: AccessStatus,
    is_admin: bool = False,
    is_active: bool = True,
) -> User:
    user = User(
        id=uuid4(),
        email=email,
        full_name=email.split("@")[0],
        password_hash=hash_password("password123"),
        access_status=status,
        is_admin=is_admin,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.flush()
    return user


def issue_csrf_headers(client: TestClient) -> dict[str, str]:
    client.get("/healthz")
    csrf_token = client.cookies.get(CSRF_COOKIE_NAME)
    assert csrf_token is not None
    return {CSRF_HEADER_NAME: csrf_token}


def test_inactive_user_cannot_login() -> None:
    factory = make_session_factory()
    with factory() as db_session:
        create_user(
            db_session,
            email="inactive@example.com",
            status=AccessStatus.APPROVED,
            is_active=False,
        )
        seed_window(db_session)
        db_session.commit()

    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        headers = issue_csrf_headers(client)
        response = client.post(
            "/api/auth/login",
            json={"email": "inactive@example.com", "password": "password123"},
            headers=headers,
        )

    assert response.status_code == 403
    payload = response.json()
    code = payload.get("detail", {}).get("code") or payload.get("error", {}).get("code")
    assert code == "user_inactive"


def test_admin_soft_delete_hides_user_from_default_list() -> None:
    factory = make_session_factory()
    with factory() as db_session:
        admin = create_user(
            db_session,
            email="admin@example.com",
            status=AccessStatus.APPROVED,
            is_admin=True,
        )
        target = create_user(
            db_session,
            email="member@example.com",
            status=AccessStatus.APPROVED,
        )
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

        delete_response = client.post(
            f"/api/admin/users/{target.id}/soft-delete",
            headers=headers,
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["is_active"] is False

        active_list_response = client.get("/api/admin/users")
        deleted_list_response = client.get("/api/admin/users?scope=deleted")

    assert active_list_response.status_code == 200
    active_ids = {row["id"] for row in active_list_response.json()}
    assert str(target.id) not in active_ids
    assert str(admin.id) in active_ids

    assert deleted_list_response.status_code == 200
    deleted_rows = deleted_list_response.json()
    assert len(deleted_rows) == 1
    assert deleted_rows[0]["id"] == str(target.id)
    assert deleted_rows[0]["is_active"] is False
