from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from app.models.schema import CompetitionPhase, SyncProvider

API_FOOTBALL_BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
API_FOOTBALL_HOST = "api-football-v1.p.rapidapi.com"


class ProviderError(Exception):
    pass


class ProviderConfigurationError(ProviderError):
    pass


class ProviderResponseError(ProviderError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderMatchRecord:
    provider: SyncProvider
    external_id: str
    starts_at: datetime
    status: str
    phase: CompetitionPhase
    stage_round: int | None
    group_name: str | None
    bracket_slot: str | None
    venue: str | None
    home_team_name: str
    away_team_name: str
    home_team_fifa_code: str | None
    away_team_fifa_code: str | None
    involves_brazil: bool
    official_home_goals: int | None
    official_away_goals: int | None
    winner_team_name: str | None
    source_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderTopScorer:
    provider: SyncProvider
    player_key: str
    player_name: str
    team_name: str | None
    goals: int
    assists: int
    source_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderSyncBatch:
    provider: SyncProvider
    fetched_at: datetime
    matches: tuple[ProviderMatchRecord, ...]
    top_scorers: tuple[ProviderTopScorer, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


def parse_timestamp(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_competition_phase(round_name: str) -> CompetitionPhase:
    normalized = round_name.strip().casefold()
    if "group stage" in normalized:
        return CompetitionPhase.GROUP_STAGE
    if "round of 32" in normalized:
        return CompetitionPhase.ROUND_OF_32
    if "round of 16" in normalized:
        return CompetitionPhase.ROUND_OF_16
    if "quarter" in normalized:
        return CompetitionPhase.QUARTER_FINAL
    if "semi" in normalized:
        return CompetitionPhase.SEMI_FINAL
    if "third" in normalized:
        return CompetitionPhase.THIRD_PLACE
    if normalized == "final":
        return CompetitionPhase.FINAL
    raise ProviderResponseError(f"unsupported competition round: {round_name}")


def parse_stage_round(round_name: str) -> int | None:
    match = re.search(r"(\d+)\s*$", round_name.strip())
    return int(match.group(1)) if match else None


class APIFootballClient:
    def __init__(
        self,
        *,
        api_key: str | None,
        league_id: int = 1,
        season: int = 2026,
        base_url: str = API_FOOTBALL_BASE_URL,
        host: str = API_FOOTBALL_HOST,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key.strip() if api_key is not None else None
        self._league_id = league_id
        self._season = season
        self._base_url = base_url.rstrip("/")
        self._host = host
        self._timeout = timeout
        self._client = client

    @property
    def provider(self) -> SyncProvider:
        return SyncProvider.API_FOOTBALL

    @property
    def configured(self) -> bool:
        return self._api_key is not None and self._api_key != ""

    def fetch_match_batch(
        self,
        *,
        fixture_ids: Sequence[str] | None = None,
        include_top_scorers: bool = False,
    ) -> ProviderSyncBatch:
        self._ensure_configured()
        fetched_at = datetime.now(timezone.utc)
        matches = self._fetch_matches_by_fixture_ids(fixture_ids) if fixture_ids else self._fetch_all_season_matches()
        top_scorers = self.fetch_top_scorers() if include_top_scorers else ()
        return ProviderSyncBatch(
            provider=self.provider,
            fetched_at=fetched_at,
            matches=matches,
            top_scorers=top_scorers,
            metadata={
                "league_id": self._league_id,
                "season": self._season,
                "requested_fixture_ids": list(fixture_ids or ()),
            },
        )

    def fetch_top_scorers(self) -> tuple[ProviderTopScorer, ...]:
        payload = self._request_json(
            "/players/topscorers",
            {"league": self._league_id, "season": self._season},
        )
        rows = payload.get("response")
        if not isinstance(rows, list):
            raise ProviderResponseError("API-Football top scorers response is missing 'response' list")
        return tuple(self._map_top_scorer_row(row) for row in rows if isinstance(row, dict))

    def _fetch_all_season_matches(self) -> tuple[ProviderMatchRecord, ...]:
        payload = self._request_json("/fixtures", {"league": self._league_id, "season": self._season})
        rows = payload.get("response")
        if not isinstance(rows, list):
            raise ProviderResponseError("API-Football fixtures response is missing 'response' list")
        return tuple(self._map_fixture_row(row) for row in rows if isinstance(row, dict))

    def _fetch_matches_by_fixture_ids(
        self,
        fixture_ids: Sequence[str],
    ) -> tuple[ProviderMatchRecord, ...]:
        matches: list[ProviderMatchRecord] = []
        for fixture_id in dict.fromkeys(fixture_ids):
            payload = self._request_json("/fixtures", {"id": fixture_id})
            rows = payload.get("response")
            if not isinstance(rows, list):
                raise ProviderResponseError(f"API-Football fixture response missing 'response' for {fixture_id}")
            matches.extend(self._map_fixture_row(row) for row in rows if isinstance(row, dict))
        return tuple(matches)

    def _map_fixture_row(self, row: Mapping[str, Any]) -> ProviderMatchRecord:
        fixture = self._expect_mapping(row.get("fixture"), "fixture")
        league = self._expect_mapping(row.get("league"), "league")
        teams = self._expect_mapping(row.get("teams"), "teams")
        home_team = self._expect_mapping(teams.get("home"), "teams.home")
        away_team = self._expect_mapping(teams.get("away"), "teams.away")
        goals_raw = self._expect_mapping(row.get("goals"), "goals")
        status_raw = self._expect_mapping(fixture.get("status"), "fixture.status")
        round_name = self._expect_str(league.get("round"), "league.round")
        home_team_name = self._expect_str(home_team.get("name"), "teams.home.name")
        away_team_name = self._expect_str(away_team.get("name"), "teams.away.name")
        home_code = self._optional_code(home_team.get("code"))
        away_code = self._optional_code(away_team.get("code"))
        home_winner = self._optional_bool(home_team.get("winner"))
        away_winner = self._optional_bool(away_team.get("winner"))
        winner_team_name = None
        if home_winner is True:
            winner_team_name = home_team_name
        elif away_winner is True:
            winner_team_name = away_team_name
        return ProviderMatchRecord(
            provider=self.provider,
            external_id=self._expect_str(fixture.get("id"), "fixture.id"),
            starts_at=parse_timestamp(self._expect_str(fixture.get("date"), "fixture.date")),
            status=self._expect_str(status_raw.get("short"), "fixture.status.short"),
            phase=parse_competition_phase(round_name),
            stage_round=parse_stage_round(round_name),
            group_name=self._parse_group_name(round_name),
            bracket_slot=None,
            venue=self._parse_venue_name(fixture.get("venue")),
            home_team_name=home_team_name,
            away_team_name=away_team_name,
            home_team_fifa_code=home_code,
            away_team_fifa_code=away_code,
            involves_brazil="BRA" in {value for value in (home_code, away_code) if value is not None},
            official_home_goals=self._optional_int(goals_raw.get("home")),
            official_away_goals=self._optional_int(goals_raw.get("away")),
            winner_team_name=winner_team_name,
            source_payload=dict(row),
        )

    def _map_top_scorer_row(self, row: Mapping[str, Any]) -> ProviderTopScorer:
        player = self._expect_mapping(row.get("player"), "player")
        statistics = row.get("statistics")
        if not isinstance(statistics, list) or not statistics:
            raise ProviderResponseError("top scorer row is missing statistics")
        stat_row = self._expect_mapping(statistics[0], "statistics[0]")
        team = self._expect_mapping(stat_row.get("team"), "statistics[0].team")
        goals = self._expect_mapping(stat_row.get("goals"), "statistics[0].goals")
        return ProviderTopScorer(
            provider=self.provider,
            player_key=self._expect_str(player.get("id"), "player.id"),
            player_name=self._expect_str(player.get("name"), "player.name"),
            team_name=self._optional_str(team.get("name")),
            goals=self._optional_int(goals.get("total")) or 0,
            assists=self._optional_int(goals.get("assists")) or 0,
            source_payload=dict(row),
        )

    def _request_json(self, path: str, params: Mapping[str, str | int]) -> dict[str, Any]:
        headers = {
            "X-RapidAPI-Key": self._api_key or "",
            "X-RapidAPI-Host": self._host,
        }
        response = self._perform_request(path, params=params, headers=headers)
        if response.status_code >= 400:
            raise ProviderResponseError(f"API-Football request failed with status {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ProviderResponseError("API-Football response must be a JSON object")
        return payload

    def _perform_request(
        self,
        path: str,
        *,
        params: Mapping[str, str | int],
        headers: Mapping[str, str],
    ) -> httpx.Response:
        if self._client is not None:
            return self._client.get(f"{self._base_url}{path}", params=params, headers=headers, timeout=self._timeout)
        with httpx.Client() as client:
            return client.get(f"{self._base_url}{path}", params=params, headers=headers, timeout=self._timeout)

    def _ensure_configured(self) -> None:
        if not self.configured:
            raise ProviderConfigurationError("API-Football client is not configured")

    def _parse_group_name(self, round_name: str) -> str | None:
        match = re.search(r"group\s+([a-z])", round_name.strip(), flags=re.IGNORECASE)
        return match.group(1).upper() if match else None

    def _parse_venue_name(self, venue_raw: Any) -> str | None:
        if isinstance(venue_raw, Mapping):
            return self._optional_str(venue_raw.get("name"))
        return None

    def _expect_mapping(self, value: Any, field_name: str) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return value
        raise ProviderResponseError(f"API-Football field '{field_name}' must be an object")

    def _expect_str(self, value: Any, field_name: str) -> str:
        if isinstance(value, str) and value.strip() != "":
            return value.strip()
        if isinstance(value, int):
            return str(value)
        raise ProviderResponseError(f"API-Football field '{field_name}' must be a non-empty string")

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        if isinstance(value, int):
            return str(value)
        return None

    def _optional_code(self, value: Any) -> str | None:
        normalized = self._optional_str(value)
        return normalized.upper() if normalized is not None else None

    def _optional_int(self, value: Any) -> int | None:
        if value is None or value == "" or isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return int(value)
        return None

    def _optional_bool(self, value: Any) -> bool | None:
        return value if isinstance(value, bool) else None
