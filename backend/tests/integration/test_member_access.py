from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, hash_password
from app.main import create_app
from app.models.schema import (
    AccessStatus,
    Base,
    CompetitionPrediction,
    CompetitionWindow,
    Match,
    MatchPrediction,
    PredictionType,
    User,
)
from app.repositories.queries import get_db_session


def configure_test_settings() -> None:
    os.environ["SESSION_COOKIE_DOMAIN"] = ""
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
    csrf_token = "test-csrf-token"
    client.cookies.set(CSRF_COOKIE_NAME, csrf_token)
    return {CSRF_HEADER_NAME: csrf_token}


def test_pending_user_cannot_access_dashboard() -> None:
    configure_test_settings()
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


def test_approved_user_sees_public_match_group_when_match_is_terminal() -> None:
    configure_test_settings()
    factory = make_session_factory()
    with factory() as db_session:
        user = create_user(db_session, email="approved@example.com", status=AccessStatus.APPROVED)
        seed_window(db_session, released=False)
        match = Match(
            external_provider=None,
            external_id="local-1",
            phase="GROUP_STAGE",
            starts_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            home_team_name="Brazil",
            away_team_name="Argentina",
            home_team_fifa_code="BRA",
            away_team_fifa_code="ARG",
            status="FT",
            official_home_goals=2,
            official_away_goals=1,
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
        response = client.get("/api/member/explore")
    assert response.status_code == 200
    payload = response.json()
    assert payload["exploreState"] == "released"
    assert payload["exploreReleased"] is True
    assert len(payload["matchGroups"]) == 1
    assert len(payload["matchPredictions"]) == 1
    assert payload["matchPredictions"][0]["matchId"] == payload["matchGroups"][0]["matchId"]


def test_approved_user_sees_only_public_explore_groups_when_partial() -> None:
    configure_test_settings()
    factory = make_session_factory()
    now = datetime.now(timezone.utc)
    with factory() as db_session:
        viewer = create_user(db_session, email="viewer@example.com", status=AccessStatus.APPROVED)
        other = create_user(db_session, email="other@example.com", status=AccessStatus.APPROVED)
        seed_window(db_session, released=False)
        public_match = Match(
            external_provider=None,
            external_id="local-public",
            phase="GROUP_STAGE",
            group_name="A",
            stage_round=1,
            starts_at=now + timedelta(minutes=10),
            home_team_name="Brazil",
            away_team_name="Argentina",
            home_team_fifa_code="BRA",
            away_team_fifa_code="ARG",
            status="SCHEDULED",
        )
        hidden_match = Match(
            external_provider=None,
            external_id="local-hidden",
            phase="GROUP_STAGE",
            group_name="B",
            stage_round=1,
            starts_at=now + timedelta(hours=2),
            home_team_name="Mexico",
            away_team_name="Japan",
            home_team_fifa_code="MEX",
            away_team_fifa_code="JPN",
            status="SCHEDULED",
        )
        db_session.add_all([public_match, hidden_match])
        db_session.flush()
        db_session.add_all(
            [
                MatchPrediction(user_id=viewer.id, match_id=public_match.id, home_goals=2, away_goals=1, points_awarded=3),
                MatchPrediction(user_id=other.id, match_id=public_match.id, home_goals=1, away_goals=1, points_awarded=1),
                MatchPrediction(user_id=viewer.id, match_id=hidden_match.id, home_goals=1, away_goals=0, points_awarded=0),
                MatchPrediction(user_id=other.id, match_id=hidden_match.id, home_goals=0, away_goals=1, points_awarded=0),
            ]
        )
        db_session.commit()
    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        headers = issue_csrf_headers(client)
        login_response = client.post(
            "/api/auth/login",
            json={"email": "viewer@example.com", "password": "password123"},
            headers=headers,
        )
        assert login_response.status_code == 200
        response = client.get("/api/member/explore")
    assert response.status_code == 200
    payload = response.json()
    assert payload["exploreState"] == "partial"
    assert len(payload["matchGroups"]) == 1
    assert len(payload["matchPredictions"]) == 2
    assert {item["matchId"] for item in payload["matchPredictions"]} == {payload["matchGroups"][0]["matchId"]}


def test_ranking_excludes_non_approved_users() -> None:
    configure_test_settings()
    factory = make_session_factory()
    with factory() as db_session:
        approved = create_user(db_session, email="approved@example.com", status=AccessStatus.APPROVED)
        create_user(db_session, email="pending@example.com", status=AccessStatus.PENDING)
        seed_window(db_session, released=True)
        exact_match = Match(
            external_provider=None,
            external_id="local-2",
            phase="GROUP_STAGE",
            starts_at=datetime.now(timezone.utc),
            home_team_name="Brazil",
            away_team_name="Japan",
            home_team_fifa_code="BRA",
            away_team_fifa_code="JPN",
            involves_brazil=True,
            status="FT",
            official_home_goals=1,
            official_away_goals=0,
        )
        result_match = Match(
            external_provider=None,
            external_id="local-3",
            phase="GROUP_STAGE",
            starts_at=datetime.now(timezone.utc),
            home_team_name="Mexico",
            away_team_name="Japan",
            home_team_fifa_code="MEX",
            away_team_fifa_code="JPN",
            status="FT",
            official_home_goals=1,
            official_away_goals=0,
        )
        db_session.add_all([exact_match, result_match])
        db_session.flush()
        db_session.add(
            MatchPrediction(
                user_id=approved.id,
                match_id=exact_match.id,
                home_goals=1,
                away_goals=0,
                points_awarded=6,
            )
        )
        db_session.add(
            MatchPrediction(
                user_id=approved.id,
                match_id=result_match.id,
                home_goals=2,
                away_goals=1,
                points_awarded=1,
            )
        )
        db_session.add(
            CompetitionPrediction(
                user_id=approved.id,
                prediction_type=PredictionType.CHAMPION,
                selection_key="BRA",
                selection_label="Brazil",
                points_awarded=10,
            )
        )
        db_session.add(
            CompetitionPrediction(
                user_id=approved.id,
                prediction_type=PredictionType.TOP_SCORER,
                selection_key="NEY",
                selection_label="Neymar",
                points_awarded=15,
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
    payload = response.json()
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["fullName"] == "approved"
    assert payload["rows"][0]["exactPoints"] == 3
    assert payload["rows"][0]["resultPoints"] == 1
    assert payload["rows"][0]["brazilPoints"] == 3
    assert payload["currentUserBreakdown"] == {
        "matchPoints": 7,
        "exactPoints": 3,
        "resultPoints": 1,
        "brazilPoints": 3,
        "championPoints": 10,
        "topScorerPoints": 15,
        "bonusPoints": 25,
        "totalPoints": 32,
    }


def test_approved_user_sees_released_predictions_with_match_metadata() -> None:
    configure_test_settings()
    factory = make_session_factory()
    with factory() as db_session:
        viewer = create_user(db_session, email="viewer@example.com", status=AccessStatus.APPROVED)
        other = create_user(db_session, email="other@example.com", status=AccessStatus.APPROVED)
        hidden = create_user(db_session, email="hidden@example.com", status=AccessStatus.PENDING)
        seed_window(db_session, released=True)
        match = Match(
            external_provider=None,
            external_id="local-3",
            phase="GROUP_STAGE",
            group_name="A",
            stage_round=1,
            starts_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            home_team_name="Brazil",
            away_team_name="Argentina",
            home_team_fifa_code="BRA",
            away_team_fifa_code="ARG",
            status="FT",
            official_home_goals=2,
            official_away_goals=1,
        )
        db_session.add(match)
        db_session.flush()
        db_session.add_all(
            [
                MatchPrediction(user_id=viewer.id, match_id=match.id, home_goals=2, away_goals=1, points_awarded=3),
                MatchPrediction(user_id=other.id, match_id=match.id, home_goals=1, away_goals=1, points_awarded=1),
                MatchPrediction(user_id=hidden.id, match_id=match.id, home_goals=0, away_goals=1, points_awarded=0),
            ]
        )
        db_session.commit()
    app = create_app()
    app.dependency_overrides[get_db_session] = build_db_override(factory)
    with TestClient(app) as client:
        headers = issue_csrf_headers(client)
        login_response = client.post(
            "/api/auth/login",
            json={"email": "viewer@example.com", "password": "password123"},
            headers=headers,
        )
        assert login_response.status_code == 200
        response = client.get("/api/member/explore")
    assert response.status_code == 200
    payload = response.json()
    assert payload["exploreReleased"] is True
    assert payload["exploreState"] == "released"
    assert len(payload["matchGroups"]) == 1
    assert len(payload["matchPredictions"]) == 2
    visible_names = {item["userName"] for item in payload["matchPredictions"]}
    assert visible_names == {"viewer", "other"}
    first_prediction = payload["matchPredictions"][0]
    assert first_prediction["groupName"] == "A"
    assert first_prediction["stageRound"] == 1
    assert first_prediction["homeTeam"] == "Brasil"
    assert first_prediction["awayTeam"] == "Argentina"
    assert first_prediction["homeFlag"] == "🇧🇷"
    assert first_prediction["awayFlag"] == "🇦🇷"
