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
from app.integrations.the_sports_db_utils import (
    THE_SPORTS_DB_BASE_URL,
    THE_SPORTS_DB_LEAGUE_ID,
    TheSportsDBEventResult,
    normalize_event_row,
)


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
        requested_fixture_ids = set(fixture_ids or ())
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
            if not requested_fixture_ids or match.external_id in requested_fixture_ids
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
        normalized = normalize_event_row(row)
        if normalized is None:
            return ()
        return (
            ProviderMatchRecord(
                provider=self.provider,
                external_id=normalized.event_id,
                starts_at=normalized.starts_at,
                status=normalized.status,
                phase=CompetitionPhase.GROUP_STAGE,
                stage_round=normalized.round,
                group_name=get_team_metadata(normalized.home_code).group,
                bracket_slot=None,
                venue=self._optional_str(row.get("strVenue")),
                home_team_name=normalized.home_name,
                away_team_name=normalized.away_name,
                home_team_fifa_code=normalized.home_code,
                away_team_fifa_code=normalized.away_code,
                involves_brazil="BRA" in {normalized.home_code, normalized.away_code},
                official_home_goals=normalized.home_goals,
                official_away_goals=normalized.away_goals,
                winner_team_name=self._winner_name(normalized),
                source_payload=normalized.source_payload,
            ),
        )

    def _winner_name(self, normalized: TheSportsDBEventResult) -> str | None:
        if normalized.home_goals is None or normalized.away_goals is None:
            return None
        if normalized.home_goals > normalized.away_goals:
            return normalized.home_name
        if normalized.away_goals > normalized.home_goals:
            return normalized.away_name
        return None

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

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        if isinstance(value, int):
            return str(value)
        return None
