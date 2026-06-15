from __future__ import annotations

import httpx

from app.integrations.the_sports_db import TheSportsDBClient
from app.integrations.the_sports_db_utils import list_recent_result_payloads


def test_the_sports_db_maps_group_stage_event_to_local_codes() -> None:
    payload = {
        "events": [
            {
                "idEvent": "2391728",
                "strHomeTeam": "Mexico",
                "strAwayTeam": "South Africa",
                "intRound": "1",
                "intHomeScore": "2",
                "intAwayScore": "0",
                "strTimestamp": "2026-06-11T19:00:00",
                "strVenue": "Estadio Azteca",
                "strStatus": "FT",
            }
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/eventsseason.php")
        return httpx.Response(200, json=payload)

    client = TheSportsDBClient(client=httpx.Client(transport=httpx.MockTransport(handler)))
    batch = client.fetch_match_batch()

    assert batch.provider.value == "THE_SPORTS_DB"
    assert len(batch.matches) == 1
    match = batch.matches[0]
    assert match.external_id == "2391728"
    assert match.phase.value == "GROUP_STAGE"
    assert match.stage_round == 1
    assert match.group_name == "A"
    assert match.home_team_fifa_code == "MEX"
    assert match.away_team_fifa_code == "RSA"
    assert match.home_team_name == "México"
    assert match.away_team_name == "África do Sul"
    assert match.official_home_goals == 2
    assert match.official_away_goals == 0
    assert match.status == "FT"


def test_the_sports_db_skips_unknown_team_aliases() -> None:
    payload = {
        "events": [
            {
                "idEvent": "1",
                "strHomeTeam": "Unknown Team",
                "strAwayTeam": "South Africa",
                "intRound": "1",
                "strTimestamp": "2026-06-11T19:00:00",
                "strStatus": "FT",
            }
        ]
    }

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = TheSportsDBClient(client=httpx.Client(transport=httpx.MockTransport(handler)))
    batch = client.fetch_match_batch()

    assert batch.matches == ()


def test_list_recent_result_payloads_returns_latest_finished_results() -> None:
    rows = [
        {
            "idEvent": "2391728",
            "strHomeTeam": "Mexico",
            "strAwayTeam": "South Africa",
            "intRound": "1",
            "intHomeScore": "2",
            "intAwayScore": "0",
            "dateEvent": "2026-06-11",
            "strTime": "19:00:00",
            "strTimestamp": "2026-06-11T19:00:00",
            "strStatus": "FT",
            "idLeague": "4429",
            "strLeague": "FIFA World Cup",
            "strSeason": "2026",
        },
        {
            "idEvent": "2391729",
            "strHomeTeam": "USA",
            "strAwayTeam": "Paraguay",
            "intRound": "1",
            "intHomeScore": "4",
            "intAwayScore": "1",
            "dateEvent": "2026-06-13",
            "strTime": "01:00:00",
            "strTimestamp": "2026-06-13T01:00:00",
            "strStatus": "FT",
            "idLeague": "4429",
            "strLeague": "FIFA World Cup",
            "strSeason": "2026",
        },
    ]

    results = list_recent_result_payloads(rows, limit=1)

    assert len(results) == 1
    assert results[0]["event_id"] == "2391729"
    assert results[0]["home"]["name"] == "Estados Unidos"
    assert results[0]["away"]["name"] == "Paraguai"
    assert results[0]["result"]["score"] == "4x1"
    assert results[0]["result"]["winner"] == {"name": "Estados Unidos", "tag": "USA"}
