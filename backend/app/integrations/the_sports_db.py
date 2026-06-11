from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.integrations.api_football import (
    ProviderMatchRecord,
    ProviderResponseError,
    ProviderSyncBatch,
    ProviderTopScorer,
)
from app.models.schema import CompetitionPhase, SyncProvider
from app.services.team_metadata import get_team_metadata

THE_SPORTS_DB_BASE_URL = "https://www.thesportsdb.com/api/v1/json/123"
THE_SPORTS_DB_LEAGUE_ID = "4429"

THE_SPORTS_DB_TEAM_ALIASES: dict[str, str] = {
    "mexico": "MEX",
    "south africa": "RSA",
    "south korea": "KOR",
    "czech republic": "CZE",
    "canada": "CAN",
    "bosnia-herzegovina": "BIH",
    "qatar": "QAT",
    "switzerland": "SUI",
    "brazil": "BRA",
    "morocco": "MAR",
    "haiti": "HAI",
    "scotland": "SCO",
    "usa": "USA",
    "paraguay": "PAR",
    "australia": "AUS",
    "turkey": "TUR",
    "germany": "GER",
    "curacao": "CUW",
    "ivory coast": "CIV",
    "ecuador": "ECU",
    "netherlands": "NED",
    "japan": "JPN",
    "sweden": "SWE",
    "tunisia": "TUN",
    "belgium": "BEL",
    "egypt": "EGY",
    "iran": "IRN",
    "new zealand": "NZL",
    "spain": "ESP",
    "cape verde": "CPV",
    "saudi arabia": "KSA",
    "uruguay": "URU",
    "france": "FRA",
    "senegal": "SEN",
    "iraq": "IRQ",
    "norway": "NOR",
    "argentina": "ARG",
    "algeria": "ALG",
    "austria": "AUT",
    "jordan": "JOR",
    "portugal": "POR",
    "dr congo": "COD",
    "uzbekistan": "UZB",
    "colombia": "COL",
    "england": "ENG",
    "croatia": "CRO",
    "ghana": "GHA",
    "panama": "PAN",
}

THE_SPORTS_DB_STATUS_MAP: dict[str, str] = {
    "ns": "NS",
    "ft": "FT",
    "aet": "AET",
    "pen": "PEN",
    "postponed": "POSTPONED",
    "cancelled": "CANCELLED",
    "abd": "ABANDONED",
    "live": "LIVE",
    "ht": "HT",
}


@dataclass(frozen=True, slots=True)
class TheSportsDBSettings:
    base_url: str = THE_SPORTS_DB_BASE_URL
    league_id: str = THE_SPORTS_DB_LEAGUE_ID
    season: str = "2026"


class TheSportsDBClient:
    def __init__(
        self,
        *,
        settings: TheSportsDBSettings | None = None,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings or TheSportsDBSettings()
        self._timeout = timeout
        self._client = client

    @property
    def provider(self) -> SyncProvider:
        return SyncProvider.THE_SPORTS_DB

    @property
    def configured(self) -> bool:
        return True

    def fetch_match_batch(
        self,
        *,
        fixture_ids: Sequence[str] | None = None,
        include_top_scorers: bool = False,
    ) -> ProviderSyncBatch:
        del include_top_scorers
        payload = self._request_json(
            "/eventsseason.php",
            {
                "id": self._settings.league_id,
                "s": self._settings.season,
            },
        )
        rows = payload.get("events")
        if not isinstance(rows, list):
            raise ProviderResponseError("TheSportsDB response is missing 'events'")

        matches = tuple(
            match
            for row in rows
            if isinstance(row, dict)
            for match in self._map_event_row(row)
            if fixture_ids is None or match.external_id in set(fixture_ids)
        )
        return ProviderSyncBatch(
            provider=self.provider,
            fetched_at=datetime.now(timezone.utc),
            matches=matches,
            top_scorers=(),
            metadata={
                "league_id": self._settings.league_id,
                "season": self._settings.season,
                "requested_fixture_ids": list(fixture_ids or ()),
            },
        )

    def fetch_top_scorers(self) -> tuple[ProviderTopScorer, ...]:
        return ()

    def _map_event_row(self, row: Mapping[str, Any]) -> tuple[ProviderMatchRecord, ...]:
        event_id = self._require_str(row.get("idEvent"), "idEvent")
        provider_home_name = self._require_str(row.get("strHomeTeam"), "strHomeTeam")
        provider_away_name = self._require_str(row.get("strAwayTeam"), "strAwayTeam")
        home_code = self._provider_name_to_code(provider_home_name)
        away_code = self._provider_name_to_code(provider_away_name)
        if home_code is None or away_code is None:
            return ()

        home_team = get_team_metadata(home_code)
        away_team = get_team_metadata(away_code)
        if home_team.group is None or away_team.group is None or home_team.group != away_team.group:
            return ()

        round_number = self._optional_int(row.get("intRound"))
        if round_number not in {1, 2, 3}:
            return ()

        starts_at = self._parse_timestamp(
            self._require_str(row.get("strTimestamp"), "strTimestamp")
        )
        status = self._normalize_status(row.get("strStatus"))
        home_goals = self._optional_int(row.get("intHomeScore"))
        away_goals = self._optional_int(row.get("intAwayScore"))
        winner_team_name = None
        if home_goals is not None and away_goals is not None:
            if home_goals > away_goals:
                winner_team_name = home_team.name
            elif away_goals > home_goals:
                winner_team_name = away_team.name

        return (
            ProviderMatchRecord(
                provider=self.provider,
                external_id=event_id,
                starts_at=starts_at,
                status=status,
                phase=CompetitionPhase.GROUP_STAGE,
                stage_round=round_number,
                group_name=home_team.group,
                bracket_slot=None,
                venue=self._optional_str(row.get("strVenue")),
                home_team_name=home_team.name,
                away_team_name=away_team.name,
                home_team_fifa_code=home_team.code,
                away_team_fifa_code=away_team.code,
                involves_brazil="BRA" in {home_team.code, away_team.code},
                official_home_goals=home_goals,
                official_away_goals=away_goals,
                winner_team_name=winner_team_name,
                source_payload=dict(row),
            ),
        )

    def _request_json(self, path: str, params: Mapping[str, str]) -> dict[str, Any]:
        response = self._perform_request(
            f"{self._settings.base_url}{path}",
            params=params,
        )
        if response.status_code >= 400:
            raise ProviderResponseError(
                f"TheSportsDB request failed with status {response.status_code}"
            )
        payload = response.json()
        if not isinstance(payload, dict):
            raise ProviderResponseError("TheSportsDB response must be a JSON object")
        return payload

    def _perform_request(self, url: str, *, params: Mapping[str, str]) -> httpx.Response:
        if self._client is not None:
            return self._client.get(url, params=params, timeout=self._timeout)
        with httpx.Client() as client:
            return client.get(url, params=params, timeout=self._timeout)

    def _provider_name_to_code(self, name: str) -> str | None:
        normalized = name.strip().casefold()
        return THE_SPORTS_DB_TEAM_ALIASES.get(normalized)

    def _normalize_status(self, value: Any) -> str:
        raw = self._optional_str(value)
        if raw is None:
            return "UNKNOWN"
        return THE_SPORTS_DB_STATUS_MAP.get(raw.casefold(), raw.strip().upper())

    def _parse_timestamp(self, value: str) -> datetime:
        parsed = datetime.fromisoformat(value.strip())
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _require_str(self, value: Any, field_name: str) -> str:
        normalized = self._optional_str(value)
        if normalized is None:
            raise ProviderResponseError(
                f"TheSportsDB field '{field_name}' must be a non-empty string"
            )
        return normalized

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        if isinstance(value, int):
            return str(value)
        return None

    def _optional_int(self, value: Any) -> int | None:
        if value is None or value == "" or isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return int(value)
        return None
