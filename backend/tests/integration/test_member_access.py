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
from app.models.schema import (
    AccessStatus,
    Base,
    CompetitionWindow,
    Match,
    MatchPrediction,
    User,
)
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


def create_user(db_session: Session, *, email: str, status: AccessStatus) -> User:
    user = User(
        id=uuid4(),
        email=email,
        full_name=email.split("@")[0],
        password_hash=hash_password("password123"),
        access_status=status,
        is_admin=False,
    )
    db_session.add(user)
    db_session.flush()
    return user


def seed_window(db_session: Session, *, released: bool) -> None:
    now = datetime.now(timezone.utc)
    db_session.add(
        CompetitionWindow(
            name="default",
            prediction_close_at=now + timedelta(hours=1),
            explore_release_at=now - timedelta(hours=1) if released else now + timedelta(hours=1),
            is_active=True,
        )
    )
    db_session.flush()


def issue_csrf_headers(client: TestClient) -> dict[str, str]:
    client.get("/healthz")
    csrf_token = client.cookies.get(CSRF_COOKIE_NAME)
    assert csrf_token is not None
    return {CSRF_HEADER_NAME: csrf_token}


def test_pending_user_cannot_access_dashboard() -> None:
    factory = make_session_factory()
    with factory() as db_session:
        create_user(db_session, email="pending@example.com", status=AccessStatus.PENDING)
        seed_window(db_session, released=False)
        db_session.commit()
    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        headers = issue_csrf_headers(client)
        login_response = client.post(
            "/api/auth/login",
            json={"email": "pending@example.com", "password": "password123"},
            headers=headers,
        )
        assert login_response.status_code == 200
        response = client.get("/api/member/dashboard")
    assert response.status_code == 403


def test_approved_user_can_save_prediction_and_see_own_explore_before_release() -> None:
    factory = make_session_factory()
    with factory() as db_session:
        user = create_user(db_session, email="approved@example.com", status=AccessStatus.APPROVED)
        seed_window(db_session, released=False)
        match = Match(
            external_provider=None,
            external_id="local-1",
            phase="GROUP_STAGE",
            starts_at=datetime.now(timezone.utc) + timedelta(days=1),
            home_team_name="Brazil",
            away_team_name="Argentina",
            home_team_fifa_code="BRA",
            away_team_fifa_code="ARG",
            status="SCHEDULED",
        )
        db_session.add(match)
        db_session.flush()
        db_session.add(
            MatchPrediction(
                user_id=user.id,
                match_id=match.id,
                home_goals=2,
                away_goals=1,
            )
        )
        db_session.commit()
    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        headers = issue_csrf_headers(client)
        login_response = client.post(
            "/api/auth/login",
            json={"email": "approved@example.com", "password": "password123"},
            headers=headers,
        )
        assert login_response.status_code == 200
        save_response = client.put(
            f"/api/member/predictions/matches/{match.id}",
            json={"home_goals": 1, "away_goals": 0},
            headers=headers,
        )
        assert save_response.status_code == 200
        response = client.get("/api/member/explore")
    assert response.status_code == 200
    assert response.json()["exploreReleased"] is False
    assert len(response.json()["matchPredictions"]) == 1


def test_ranking_excludes_non_approved_users() -> None:
    factory = make_session_factory()
    with factory() as db_session:
        approved = create_user(db_session, email="approved@example.com", status=AccessStatus.APPROVED)
        create_user(db_session, email="pending@example.com", status=AccessStatus.PENDING)
        seed_window(db_session, released=True)
        match = Match(
            external_provider=None,
            external_id="local-2",
            phase="GROUP_STAGE",
            starts_at=datetime.now(timezone.utc),
            home_team_name="Brazil",
            away_team_name="Japan",
            home_team_fifa_code="BRA",
            away_team_fifa_code="JPN",
            status="FT",
            official_home_goals=1,
            official_away_goals=0,
        )
        db_session.add(match)
        db_session.flush()
        db_session.add(
            MatchPrediction(
                user_id=approved.id,
                match_id=match.id,
                home_goals=1,
                away_goals=0,
                points_awarded=6,
            )
        )
        db_session.commit()
    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        headers = issue_csrf_headers(client)
        login_response = client.post(
            "/api/auth/login",
            json={"email": "approved@example.com", "password": "password123"},
            headers=headers,
        )
        assert login_response.status_code == 200
        response = client.get("/api/member/ranking")
    assert response.status_code == 200
    assert len(response.json()["rows"]) == 1
    assert response.json()["rows"][0]["fullName"] == "approved"
