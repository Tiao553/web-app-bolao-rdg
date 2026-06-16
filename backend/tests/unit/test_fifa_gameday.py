from __future__ import annotations

from datetime import datetime, timezone

from app.integrations.api_football import ProviderMatchRecord, ProviderSyncBatch
from app.integrations.fifa_gameday import FifaGamedayClient
from app.models.schema import CompetitionPhase, SyncProvider


def build_batch() -> ProviderSyncBatch:
    return ProviderSyncBatch(
        provider=SyncProvider.THE_SPORTS_DB,
        fetched_at=datetime.now(timezone.utc),
        matches=(
            ProviderMatchRecord(
                provider=SyncProvider.THE_SPORTS_DB,
                external_id="111",
                starts_at=datetime.now(timezone.utc),
                status="FT",
                phase=CompetitionPhase.GROUP_STAGE,
                stage_round=None,
                group_name="A",
                bracket_slot=None,
                venue=None,
                home_team_name="A",
                away_team_name="B",
                home_team_fifa_code="AAA",
                away_team_fifa_code="BBB",
                involves_brazil=False,
                official_home_goals=1,
                official_away_goals=0,
                winner_team_name="A",
                source_payload={},
            ),
            ProviderMatchRecord(
                provider=SyncProvider.THE_SPORTS_DB,
                external_id="222",
                starts_at=datetime.now(timezone.utc),
                status="FT",
                phase=CompetitionPhase.GROUP_STAGE,
                stage_round=None,
                group_name="B",
                bracket_slot=None,
                venue=None,
                home_team_name="C",
                away_team_name="D",
                home_team_fifa_code="CCC",
                away_team_fifa_code="DDD",
                involves_brazil=False,
                official_home_goals=2,
                official_away_goals=2,
                winner_team_name=None,
                source_payload={},
            ),
        ),
        top_scorers=(),
        metadata={},
    )


def test_fifa_gameday_client_returns_empty_batch_when_fixture_filter_misses(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integrations.fifa_gameday.scrape_recent_results_batch",
        lambda *, limit, headless: build_batch(),
    )

    batch = FifaGamedayClient().fetch_match_batch(fixture_ids=("does-not-exist",))

    assert batch.matches == ()
    assert batch.metadata["requested_fixture_ids"] == ["does-not-exist"]
    assert batch.metadata["requested_fixture_match_count"] == 0


def test_fifa_gameday_client_filters_to_requested_fixture_ids(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.integrations.fifa_gameday.scrape_recent_results_batch",
        lambda *, limit, headless: build_batch(),
    )

    batch = FifaGamedayClient().fetch_match_batch(fixture_ids=("222",))

    assert len(batch.matches) == 1
    assert batch.matches[0].external_id == "222"
    assert batch.metadata["requested_fixture_ids"] == ["222"]
    assert batch.metadata["requested_fixture_match_count"] == 1
