from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from typing import cast
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, hash_password
from app.main import create_app
from app.integrations.api_football import (
    APIFootballClient,
    ProviderMatchRecord,
    ProviderSyncBatch,
)
from app.integrations.google_sheets import GoogleSheetsClient
from app.integrations.the_sports_db import TheSportsDBClient
from app.models.schema import (
    AccessStatus,
    Base,
    CompetitionPhase,
    CompetitionWindow,
    Match,
    MatchPrediction,
    SyncLog,
    SyncProvider,
    User,
)
from app.api.routes.admin import MatchManualOverrideRequest, update_match_manual_override
from app.repositories.queries import get_db_session
from app.services.recalculation_service import recalculate_match_prediction_points
from app.services.sync_service import SyncRunResult, SyncService


class FakeApiFootballClient:
    provider = SyncProvider.API_FOOTBALL
    configured = True

    def __init__(self, batch: ProviderSyncBatch) -> None:
        self._batch = batch

    def fetch_match_batch(self, **_: object) -> ProviderSyncBatch:
        return self._batch


class FakeTheSportsDBClient:
    provider = SyncProvider.THE_SPORTS_DB
    configured = True

    def __init__(self, batch: ProviderSyncBatch) -> None:
        self._batch = batch

    def fetch_match_batch(self, **_: object) -> ProviderSyncBatch:
        return self._batch


class FakeGoogleSheetsClient:
    provider = SyncProvider.GOOGLE_SHEETS
    configured = False

    def fetch_match_batch(self, **_: object) -> ProviderSyncBatch:
        raise AssertionError("fallback should not be used in this test")


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    return factory()


def make_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def db_override(factory: sessionmaker[Session]):
    db_session = factory()
    try:
        yield db_session
        db_session.commit()
    finally:
        db_session.close()


def build_db_override(factory: sessionmaker[Session]):
    def override():
        yield from db_override(factory)

    return override


def issue_csrf_headers(client: TestClient) -> dict[str, str]:
    client.get("/healthz")
    csrf_token = client.cookies.get(CSRF_COOKIE_NAME)
    assert csrf_token is not None
    return {CSRF_HEADER_NAME: csrf_token}


def configure_test_settings() -> None:
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
    os.environ["SESSION_COOKIE_DOMAIN"] = ""
    os.environ["SYNC_ADMIN_TOKEN"] = "secret-token"
    get_settings.cache_clear()


def create_admin(db_session: Session) -> User:
    admin = User(
        id=uuid4(),
        email="admin@example.com",
        full_name="admin",
        password_hash=hash_password("password123"),
        access_status=AccessStatus.APPROVED,
        is_admin=True,
    )
    db_session.add(admin)
    db_session.flush()
    return admin


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


def test_sync_service_skips_manual_override_and_preserves_match() -> None:
    db_session = make_session()
    try:
        create_admin(db_session)
        match = Match(
            external_provider=SyncProvider.API_FOOTBALL,
            external_id="fixture-1",
            phase=CompetitionPhase.GROUP_STAGE,
            starts_at=datetime.now(timezone.utc) - timedelta(hours=3),
            home_team_name="Brazil",
            away_team_name="Argentina",
            home_team_fifa_code="BRA",
            away_team_fifa_code="ARG",
            status="FT",
            official_home_goals=2,
            official_away_goals=1,
            has_manual_override=True,
        )
        db_session.add(match)
        db_session.flush()
        batch = ProviderSyncBatch(
            provider=SyncProvider.API_FOOTBALL,
            fetched_at=datetime.now(timezone.utc),
            matches=(
                ProviderMatchRecord(
                    provider=SyncProvider.API_FOOTBALL,
                    external_id="fixture-1",
                    starts_at=match.starts_at,
                    status="FT",
                    phase=CompetitionPhase.GROUP_STAGE,
                    stage_round=1,
                    group_name="A",
                    bracket_slot=None,
                    venue="venue",
                    home_team_name="Brazil",
                    away_team_name="Argentina",
                    home_team_fifa_code="BRA",
                    away_team_fifa_code="ARG",
                    involves_brazil=True,
                    official_home_goals=3,
                    official_away_goals=0,
                    winner_team_name="Brazil",
                ),
            ),
            top_scorers=(),
        )
        service = SyncService(
            the_sports_db_client=cast(TheSportsDBClient, FakeTheSportsDBClient(batch)),
            api_football_client=cast(APIFootballClient, FakeApiFootballClient(batch)),
            google_sheets_client=cast(GoogleSheetsClient, FakeGoogleSheetsClient()),
        )
        result = service.run_scheduled_sync(db_session)
        assert result.skipped_count == 1
        assert match.official_home_goals == 2
        assert match.official_away_goals == 1
    finally:
        db_session.close()


def test_sync_service_updates_match_when_override_absent() -> None:
    db_session = make_session()
    try:
        create_admin(db_session)
        starts_at = datetime.now(timezone.utc) - timedelta(hours=3)
        match = Match(
            external_provider=SyncProvider.API_FOOTBALL,
            external_id="fixture-2",
            phase=CompetitionPhase.GROUP_STAGE,
            starts_at=starts_at,
            home_team_name="Brazil",
            away_team_name="Japan",
            home_team_fifa_code="BRA",
            away_team_fifa_code="JPN",
            status="SCHEDULED",
        )
        db_session.add(match)
        db_session.flush()
        batch = ProviderSyncBatch(
            provider=SyncProvider.API_FOOTBALL,
            fetched_at=datetime.now(timezone.utc),
            matches=(
                ProviderMatchRecord(
                    provider=SyncProvider.API_FOOTBALL,
                    external_id="fixture-2",
                    starts_at=starts_at,
                    status="FT",
                    phase=CompetitionPhase.GROUP_STAGE,
                    stage_round=1,
                    group_name="C",
                    bracket_slot=None,
                    venue="venue",
                    home_team_name="Brazil",
                    away_team_name="Japan",
                    home_team_fifa_code="BRA",
                    away_team_fifa_code="JPN",
                    involves_brazil=True,
                    official_home_goals=1,
                    official_away_goals=0,
                    winner_team_name="Brazil",
                ),
            ),
            top_scorers=(),
        )
        service = SyncService(
            the_sports_db_client=cast(TheSportsDBClient, FakeTheSportsDBClient(batch)),
            api_football_client=cast(APIFootballClient, FakeApiFootballClient(batch)),
            google_sheets_client=cast(GoogleSheetsClient, FakeGoogleSheetsClient()),
        )
        result = service.run_scheduled_sync(db_session)
        assert result.success_count == 1
        assert match.status == "FT"
        assert match.official_home_goals == 1
        assert match.official_away_goals == 0
    finally:
        db_session.close()


def test_sync_service_matches_seeded_match_by_team_codes_and_kickoff() -> None:
    db_session = make_session()
    try:
        create_admin(db_session)
        starts_at = datetime.now(timezone.utc) - timedelta(hours=3)
        match = Match(
            external_provider=SyncProvider.SEED,
            external_id="17",
            phase=CompetitionPhase.GROUP_STAGE,
            stage_round=3,
            group_name="C",
            starts_at=starts_at,
            home_team_name="BRA",
            away_team_name="SCO",
            home_team_fifa_code="BRA",
            away_team_fifa_code="SCO",
            status="SCHEDULED",
        )
        db_session.add(match)
        db_session.flush()
        batch = ProviderSyncBatch(
            provider=SyncProvider.THE_SPORTS_DB,
            fetched_at=datetime.now(timezone.utc),
            matches=(
                ProviderMatchRecord(
                    provider=SyncProvider.THE_SPORTS_DB,
                    external_id="2391728",
                    starts_at=starts_at,
                    status="FT",
                    phase=CompetitionPhase.GROUP_STAGE,
                    stage_round=3,
                    group_name="C",
                    bracket_slot=None,
                    venue="hard_rock_stadium",
                    home_team_name="Brasil",
                    away_team_name="Escócia",
                    home_team_fifa_code="BRA",
                    away_team_fifa_code="SCO",
                    involves_brazil=True,
                    official_home_goals=2,
                    official_away_goals=0,
                    winner_team_name="Brasil",
                ),
            ),
            top_scorers=(),
        )
        service = SyncService(
            the_sports_db_client=cast(TheSportsDBClient, FakeTheSportsDBClient(batch)),
            api_football_client=cast(APIFootballClient, FakeApiFootballClient(batch)),
            google_sheets_client=cast(GoogleSheetsClient, FakeGoogleSheetsClient()),
        )

        result = service.run_scheduled_sync(db_session, requested_provider=SyncProvider.THE_SPORTS_DB)

        assert result.success_count == 1
        assert match.external_provider is SyncProvider.THE_SPORTS_DB
        assert match.external_id == "2391728"
        assert match.status == "FT"
        assert match.official_home_goals == 2
        assert match.official_away_goals == 0
    finally:
        db_session.close()


def test_sync_service_logs_missing_local_match_for_scheduled_sync() -> None:
    db_session = make_session()
    try:
        create_admin(db_session)
        batch = ProviderSyncBatch(
            provider=SyncProvider.THE_SPORTS_DB,
            fetched_at=datetime.now(timezone.utc),
            matches=(
                ProviderMatchRecord(
                    provider=SyncProvider.THE_SPORTS_DB,
                    external_id="missing-1",
                    starts_at=datetime.now(timezone.utc) - timedelta(hours=3),
                    status="FT",
                    phase=CompetitionPhase.GROUP_STAGE,
                    stage_round=1,
                    group_name="A",
                    bracket_slot=None,
                    venue="venue",
                    home_team_name="México",
                    away_team_name="África do Sul",
                    home_team_fifa_code="MEX",
                    away_team_fifa_code="RSA",
                    involves_brazil=False,
                    official_home_goals=1,
                    official_away_goals=0,
                    winner_team_name="México",
                ),
            ),
            top_scorers=(),
        )
        service = SyncService(
            the_sports_db_client=cast(TheSportsDBClient, FakeTheSportsDBClient(batch)),
            api_football_client=cast(APIFootballClient, FakeApiFootballClient(batch)),
            google_sheets_client=cast(GoogleSheetsClient, FakeGoogleSheetsClient()),
        )

        result = service.run_scheduled_sync(db_session, requested_provider=SyncProvider.THE_SPORTS_DB)

        assert result.skipped_count == 1
        db_session.flush()
        log = db_session.scalar(select(SyncLog).order_by(SyncLog.created_at.desc(), SyncLog.id.desc()))
        assert log is not None
        assert log.result_code == "missing_local_match"
    finally:
        db_session.close()


def test_sync_service_latest_result_sync_uses_latest_persistable_match() -> None:
    db_session = make_session()
    try:
        create_admin(db_session)
        now = datetime.now(timezone.utc)
        latest_match = Match(
            external_provider=SyncProvider.THE_SPORTS_DB,
            external_id="latest-1",
            phase=CompetitionPhase.GROUP_STAGE,
            stage_round=1,
            group_name="A",
            starts_at=now - timedelta(hours=1),
            home_team_name="Brazil",
            away_team_name="Argentina",
            home_team_fifa_code="BRA",
            away_team_fifa_code="ARG",
            venue="venue",
            involves_brazil=True,
            status="FT",
            official_home_goals=1,
            official_away_goals=0,
            winner_team_name="Brazil",
        )
        older_match = Match(
            external_provider=SyncProvider.THE_SPORTS_DB,
            external_id="older-1",
            phase=CompetitionPhase.GROUP_STAGE,
            starts_at=now - timedelta(hours=2),
            home_team_name="Mexico",
            away_team_name="Japan",
            home_team_fifa_code="MEX",
            away_team_fifa_code="JPN",
            status="SCHEDULED",
        )
        db_session.add_all([latest_match, older_match])
        db_session.flush()
        batch = ProviderSyncBatch(
            provider=SyncProvider.THE_SPORTS_DB,
            fetched_at=now,
            matches=(
                ProviderMatchRecord(
                    provider=SyncProvider.THE_SPORTS_DB,
                    external_id="latest-1",
                    starts_at=latest_match.starts_at,
                    status="FT",
                    phase=CompetitionPhase.GROUP_STAGE,
                    stage_round=1,
                    group_name="A",
                    bracket_slot=None,
                    venue="venue",
                    home_team_name="Brazil",
                    away_team_name="Argentina",
                    home_team_fifa_code="BRA",
                    away_team_fifa_code="ARG",
                    involves_brazil=True,
                    official_home_goals=1,
                    official_away_goals=0,
                    winner_team_name="Brazil",
                ),
                ProviderMatchRecord(
                    provider=SyncProvider.THE_SPORTS_DB,
                    external_id="older-1",
                    starts_at=older_match.starts_at,
                    status="FT",
                    phase=CompetitionPhase.GROUP_STAGE,
                    stage_round=1,
                    group_name="B",
                    bracket_slot=None,
                    venue="venue",
                    home_team_name="Mexico",
                    away_team_name="Japan",
                    home_team_fifa_code="MEX",
                    away_team_fifa_code="JPN",
                    involves_brazil=False,
                    official_home_goals=2,
                    official_away_goals=0,
                    winner_team_name="Mexico",
                ),
            ),
            top_scorers=(),
        )
        service = SyncService(
            the_sports_db_client=cast(TheSportsDBClient, FakeTheSportsDBClient(batch)),
            api_football_client=cast(APIFootballClient, FakeApiFootballClient(batch)),
            google_sheets_client=cast(GoogleSheetsClient, FakeGoogleSheetsClient()),
        )

        result = service.run_latest_result_sync(db_session, requested_provider=SyncProvider.THE_SPORTS_DB)

        assert result.success_count == 1
        assert latest_match.official_home_goals == 1
        assert older_match.status == "FT"
        assert older_match.official_home_goals == 2
        db_session.flush()
        log = db_session.scalar(select(SyncLog).order_by(SyncLog.created_at.desc(), SyncLog.id.desc()))
        assert log is not None
        assert log.operation == "manual_latest_result_sync"
        assert log.match_id == older_match.id
    finally:
        db_session.close()


def test_sync_service_matches_local_record_by_team_codes_and_date_when_kickoff_differs() -> None:
    db_session = make_session()
    try:
        create_admin(db_session)
        local_starts_at = datetime(2026, 6, 11, 21, 0, tzinfo=timezone.utc)
        provider_starts_at = datetime(2026, 6, 11, 3, 0, tzinfo=timezone.utc)
        match = Match(
            external_provider=SyncProvider.THE_SPORTS_DB,
            external_id="local-1",
            phase=CompetitionPhase.GROUP_STAGE,
            starts_at=local_starts_at,
            home_team_name="México",
            away_team_name="África do Sul",
            home_team_fifa_code="MEX",
            away_team_fifa_code="RSA",
            status="SCHEDULED",
        )
        db_session.add(match)
        db_session.flush()
        batch = ProviderSyncBatch(
            provider=SyncProvider.THE_SPORTS_DB,
            fetched_at=datetime.now(timezone.utc),
            matches=(
                ProviderMatchRecord(
                    provider=SyncProvider.THE_SPORTS_DB,
                    external_id="remote-1",
                    starts_at=provider_starts_at,
                    status="FT",
                    phase=CompetitionPhase.GROUP_STAGE,
                    stage_round=1,
                    group_name="A",
                    bracket_slot=None,
                    venue="venue",
                    home_team_name="Mexico",
                    away_team_name="South Africa",
                    home_team_fifa_code="MEX",
                    away_team_fifa_code="RSA",
                    involves_brazil=False,
                    official_home_goals=2,
                    official_away_goals=0,
                    winner_team_name="Mexico",
                    source_payload={"page_index": 5},
                ),
            ),
            top_scorers=(),
        )
        service = SyncService(
            the_sports_db_client=cast(TheSportsDBClient, FakeTheSportsDBClient(batch)),
            api_football_client=cast(APIFootballClient, FakeApiFootballClient(batch)),
            google_sheets_client=cast(GoogleSheetsClient, FakeGoogleSheetsClient()),
        )

        result = service.run_scheduled_sync(db_session, requested_provider=SyncProvider.THE_SPORTS_DB)

        assert result.success_count == 1
        assert match.external_provider is SyncProvider.THE_SPORTS_DB
        assert match.status == "FT"
        assert match.official_home_goals == 2
        assert match.official_away_goals == 0
    finally:
        db_session.close()


def test_sync_service_latest_result_sync_prefers_page_index_over_kickoff_time() -> None:
    db_session = make_session()
    try:
        create_admin(db_session)
        now = datetime.now(timezone.utc)
        later_match = Match(
            external_provider=SyncProvider.THE_SPORTS_DB,
            external_id="match-a",
            phase=CompetitionPhase.GROUP_STAGE,
            starts_at=now - timedelta(hours=1),
            home_team_name="Mexico",
            away_team_name="Japan",
            home_team_fifa_code="MEX",
            away_team_fifa_code="JPN",
            status="SCHEDULED",
        )
        latest_by_page = Match(
            external_provider=SyncProvider.THE_SPORTS_DB,
            external_id="match-b",
            phase=CompetitionPhase.GROUP_STAGE,
            starts_at=now - timedelta(hours=2),
            home_team_name="Brazil",
            away_team_name="Argentina",
            home_team_fifa_code="BRA",
            away_team_fifa_code="ARG",
            status="SCHEDULED",
        )
        db_session.add_all([later_match, latest_by_page])
        db_session.flush()
        batch = ProviderSyncBatch(
            provider=SyncProvider.THE_SPORTS_DB,
            fetched_at=now,
            matches=(
                ProviderMatchRecord(
                    provider=SyncProvider.THE_SPORTS_DB,
                    external_id="match-a",
                    starts_at=later_match.starts_at,
                    status="FT",
                    phase=CompetitionPhase.GROUP_STAGE,
                    stage_round=1,
                    group_name="A",
                    bracket_slot=None,
                    venue="venue",
                    home_team_name="Mexico",
                    away_team_name="Japan",
                    home_team_fifa_code="MEX",
                    away_team_fifa_code="JPN",
                    involves_brazil=False,
                    official_home_goals=1,
                    official_away_goals=0,
                    winner_team_name="Mexico",
                    source_payload={"page_index": 3},
                ),
                ProviderMatchRecord(
                    provider=SyncProvider.THE_SPORTS_DB,
                    external_id="match-b",
                    starts_at=latest_by_page.starts_at,
                    status="FT",
                    phase=CompetitionPhase.GROUP_STAGE,
                    stage_round=1,
                    group_name="A",
                    bracket_slot=None,
                    venue="venue",
                    home_team_name="Brazil",
                    away_team_name="Argentina",
                    home_team_fifa_code="BRA",
                    away_team_fifa_code="ARG",
                    involves_brazil=True,
                    official_home_goals=2,
                    official_away_goals=0,
                    winner_team_name="Brazil",
                    source_payload={"page_index": 14},
                ),
            ),
            top_scorers=(),
        )
        service = SyncService(
            the_sports_db_client=cast(TheSportsDBClient, FakeTheSportsDBClient(batch)),
            api_football_client=cast(APIFootballClient, FakeApiFootballClient(batch)),
            google_sheets_client=cast(GoogleSheetsClient, FakeGoogleSheetsClient()),
        )

        result = service.run_latest_result_sync(db_session, requested_provider=SyncProvider.THE_SPORTS_DB)

        assert result.success_count == 1
        assert latest_by_page.status == "FT"
        assert latest_by_page.official_home_goals == 2
        assert later_match.status == "SCHEDULED"
        assert later_match.official_home_goals is None
        db_session.flush()
        log = db_session.scalar(select(SyncLog).order_by(SyncLog.created_at.desc(), SyncLog.id.desc()))
        assert log is not None
        assert log.match_id == latest_by_page.id
    finally:
        db_session.close()


def test_admin_sync_run_defaults_to_latest_result_mode(monkeypatch) -> None:
    configure_test_settings()
    factory = make_session_factory()
    with factory() as db_session:
        create_user(db_session, email="admin@example.com", status=AccessStatus.APPROVED, is_admin=True)
        seed_window(db_session)
        db_session.commit()

    calls: list[str] = []

    class FakeSyncService:
        def run_latest_result_sync(self, db_session: Session, **_: object) -> SyncRunResult:
            calls.append("latest")
            return SyncRunResult(
                provider=SyncProvider.THE_SPORTS_DB,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                outcomes=(),
                used_fallback=False,
            )

        def run_scheduled_sync(self, db_session: Session, **_: object) -> SyncRunResult:
            calls.append("scheduled")
            return SyncRunResult(
                provider=SyncProvider.THE_SPORTS_DB,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                outcomes=(),
                used_fallback=False,
            )

        def run_manual_match_sync(self, db_session: Session, **_: object) -> SyncRunResult:
            calls.append("manual")
            return SyncRunResult(
                provider=SyncProvider.THE_SPORTS_DB,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                outcomes=(),
                used_fallback=False,
            )

    monkeypatch.setattr("app.api.routes.admin.SyncService", FakeSyncService)
    monkeypatch.setattr("app.api.routes.admin.recalculate_competition_state", lambda _db: None)

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
        response = client.post(
            "/api/admin/sync/run",
            json={"provider": "THE_SPORTS_DB", "mode": "LATEST_RESULT_ONLY"},
            headers=headers,
        )

    assert response.status_code == 202
    assert calls == ["latest"]
    assert response.json()["operation"] == "manual_latest_result_sync"


def test_manual_override_normalizes_finished_status_to_ft() -> None:
    db_session = make_session()
    try:
        admin = create_admin(db_session)
        match = Match(
            external_provider=SyncProvider.API_FOOTBALL,
            external_id="fixture-3",
            phase=CompetitionPhase.GROUP_STAGE,
            starts_at=datetime.now(timezone.utc) - timedelta(hours=3),
            home_team_name="Brazil",
            away_team_name="Croatia",
            home_team_fifa_code="BRA",
            away_team_fifa_code="CRO",
            status="SCHEDULED",
        )
        db_session.add(match)
        db_session.flush()

        response = update_match_manual_override(
            match.id,
            MatchManualOverrideRequest(
                status="FINISHED",
                official_home_goals=2,
                official_away_goals=1,
                has_manual_override=True,
            ),
            admin_user=admin,
            db_session=db_session,
        )

        assert response.status == "FT"
        assert match.status == "FT"
        assert match.official_home_goals == 2
        assert match.official_away_goals == 1
    finally:
        db_session.close()


def test_recalculation_processes_finished_status_matches() -> None:
    db_session = make_session()
    try:
        admin = create_admin(db_session)
        match = Match(
            external_provider=SyncProvider.API_FOOTBALL,
            external_id="fixture-4",
            phase=CompetitionPhase.GROUP_STAGE,
            starts_at=datetime.now(timezone.utc) - timedelta(hours=3),
            home_team_name="Brazil",
            away_team_name="Japan",
            home_team_fifa_code="BRA",
            away_team_fifa_code="JPN",
            status="FINISHED",
            official_home_goals=2,
            official_away_goals=0,
        )
        db_session.add(match)
        db_session.flush()
        prediction = MatchPrediction(
            user_id=admin.id,
            match_id=match.id,
            home_goals=2,
            away_goals=0,
        )
        db_session.add(prediction)
        db_session.flush()

        summary = recalculate_match_prediction_points(db_session)

        assert summary.updated_count == 1
        assert prediction.points_awarded is not None
        assert prediction.points_awarded > 0
    finally:
        db_session.close()


def test_manual_override_applies_brazil_multiplier_for_bracket_match() -> None:
    db_session = make_session()
    try:
        admin = create_admin(db_session)
        match = Match(
            external_provider=SyncProvider.API_FOOTBALL,
            external_id="fixture-bracket-brazil",
            phase=CompetitionPhase.ROUND_OF_16,
            bracket_slot="M101",
            starts_at=datetime.now(timezone.utc) - timedelta(hours=3),
            home_team_name="Brazil",
            away_team_name="Argentina",
            home_team_fifa_code="BRA",
            away_team_fifa_code="ARG",
            involves_brazil=False,
            status="SCHEDULED",
        )
        db_session.add(match)
        db_session.flush()
        prediction = MatchPrediction(
            user_id=admin.id,
            match_id=match.id,
            home_goals=1,
            away_goals=0,
        )
        db_session.add(prediction)
        db_session.flush()

        response = update_match_manual_override(
            match.id,
            MatchManualOverrideRequest(
                status="FINISHED",
                official_home_goals=1,
                official_away_goals=0,
                has_manual_override=True,
            ),
            admin_user=admin,
            db_session=db_session,
        )

        assert response.status == "FT"
        assert match.involves_brazil is True
        assert prediction.points_awarded == 6
    finally:
        db_session.close()


def test_manual_override_recalculates_bracket_when_multiple_matches_change() -> None:
    db_session = make_session()
    try:
        admin = create_admin(db_session)
        now = datetime.now(timezone.utc)
        edited_match = Match(
            external_provider=SyncProvider.API_FOOTBALL,
            external_id="fixture-bracket-a",
            phase=CompetitionPhase.GROUP_STAGE,
            group_name="A",
            starts_at=now - timedelta(hours=3),
            home_team_name="Brazil",
            away_team_name="Argentina",
            home_team_fifa_code="BRA",
            away_team_fifa_code="ARG",
            status="SCHEDULED",
        )
        other_group_match = Match(
            external_provider=SyncProvider.API_FOOTBALL,
            external_id="fixture-bracket-b",
            phase=CompetitionPhase.GROUP_STAGE,
            group_name="B",
            starts_at=now - timedelta(hours=2),
            home_team_name="Japan",
            away_team_name="USA",
            home_team_fifa_code="JPN",
            away_team_fifa_code="USA",
            status="FT",
            official_home_goals=1,
            official_away_goals=0,
        )
        round_of_16_a = Match(
            phase=CompetitionPhase.ROUND_OF_16,
            bracket_slot="M101",
            feeder_home_key="WINNER:A",
            feeder_away_key="RUNNER_UP:B",
            starts_at=now + timedelta(days=1),
            home_team_name="Winner A",
            away_team_name="Runner-up B",
            status="SCHEDULED",
            winner_team_name="BRA",
        )
        round_of_16_b = Match(
            phase=CompetitionPhase.ROUND_OF_16,
            bracket_slot="M102",
            feeder_home_key="WINNER:B",
            feeder_away_key="RUNNER_UP:A",
            starts_at=now + timedelta(days=1, hours=2),
            home_team_name="Winner B",
            away_team_name="Runner-up A",
            status="SCHEDULED",
            winner_team_name="JPN",
        )
        semifinal = Match(
            phase=CompetitionPhase.SEMI_FINAL,
            bracket_slot="M104",
            feeder_home_key="W101",
            feeder_away_key="W102",
            starts_at=now + timedelta(days=2),
            home_team_name="Winner M101",
            away_team_name="Winner M102",
            status="SCHEDULED",
        )
        db_session.add_all(
            [edited_match, other_group_match, round_of_16_a, round_of_16_b, semifinal]
        )
        db_session.flush()

        response = update_match_manual_override(
            edited_match.id,
            MatchManualOverrideRequest(
                status="FINISHED",
                official_home_goals=2,
                official_away_goals=0,
                has_manual_override=True,
            ),
            admin_user=admin,
            db_session=db_session,
        )

        assert response.status == "FT"
        assert round_of_16_a.home_team_fifa_code == "BRA"
        assert round_of_16_a.away_team_fifa_code == "USA"
        assert round_of_16_b.home_team_fifa_code == "JPN"
        assert round_of_16_b.away_team_fifa_code == "ARG"
        assert semifinal.home_team_fifa_code == "BRA"
        assert semifinal.away_team_fifa_code == "JPN"

        log = db_session.scalar(
            select(SyncLog).order_by(SyncLog.created_at.desc(), SyncLog.id.desc())
        )
        assert log is not None
        assert log.operation == "manual_match_override"
        assert log.result_code == "manual_override_applied"
        assert log.payload is not None
        assert log.payload["bracket"]["updated_count"] >= 6
    finally:
        db_session.close()


def test_manual_override_preserves_repaired_round_of_32_pairings() -> None:
    db_session = make_session()
    try:
        admin = create_admin(db_session)
        now = datetime.now(timezone.utc)
        edited_match = Match(
            external_provider=SyncProvider.API_FOOTBALL,
            external_id="fixture-repaired-bracket-a",
            phase=CompetitionPhase.GROUP_STAGE,
            group_name="A",
            starts_at=now - timedelta(hours=3),
            home_team_name="Brazil",
            away_team_name="Argentina",
            home_team_fifa_code="BRA",
            away_team_fifa_code="ARG",
            status="SCHEDULED",
        )
        other_group_match = Match(
            external_provider=SyncProvider.API_FOOTBALL,
            external_id="fixture-repaired-bracket-b",
            phase=CompetitionPhase.GROUP_STAGE,
            group_name="B",
            starts_at=now - timedelta(hours=2),
            home_team_name="Japan",
            away_team_name="USA",
            home_team_fifa_code="JPN",
            away_team_fifa_code="USA",
            status="FT",
            official_home_goals=1,
            official_away_goals=0,
        )
        repaired_round_of_32 = Match(
            phase=CompetitionPhase.ROUND_OF_32,
            bracket_slot="M73",
            feeder_home_key="WINNER:A",
            feeder_away_key="RUNNER_UP:B",
            starts_at=now + timedelta(days=1),
            home_team_name="África do Sul",
            away_team_name="Canadá",
            home_team_fifa_code="RSA",
            away_team_fifa_code="CAN",
            status="SCHEDULED",
            source_payload={
                "manualRoundOf32Repair": {
                    "operation": "manual_round_of_32_repair_after_recalculation_regression"
                }
            },
        )
        db_session.add_all([edited_match, other_group_match, repaired_round_of_32])
        db_session.flush()

        response = update_match_manual_override(
            edited_match.id,
            MatchManualOverrideRequest(
                status="FINISHED",
                official_home_goals=2,
                official_away_goals=0,
                has_manual_override=True,
            ),
            admin_user=admin,
            db_session=db_session,
        )

        assert response.status == "FT"
        assert repaired_round_of_32.home_team_fifa_code == "RSA"
        assert repaired_round_of_32.away_team_fifa_code == "CAN"
        assert repaired_round_of_32.home_team_name == "África do Sul"
        assert repaired_round_of_32.away_team_name == "Canadá"
    finally:
        db_session.close()
