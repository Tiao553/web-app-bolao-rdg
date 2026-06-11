from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import cast
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

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
    Match,
    SyncProvider,
    User,
)
from app.services.sync_service import SyncService


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


def create_admin(db_session: Session) -> User:
    admin = User(
        id=uuid4(),
        email="admin@example.com",
        full_name="admin",
        password_hash="hash",
        access_status=AccessStatus.APPROVED,
        is_admin=True,
    )
    db_session.add(admin)
    db_session.flush()
    return admin


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
