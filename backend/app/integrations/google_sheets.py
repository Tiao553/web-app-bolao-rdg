from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from app.integrations.api_football import (
    ProviderConfigurationError,
    ProviderMatchRecord,
    ProviderResponseError,
    ProviderSyncBatch,
    ProviderTopScorer,
    parse_competition_phase,
    parse_stage_round,
    parse_timestamp,
)
from app.models.schema import SyncProvider

GOOGLE_SHEETS_BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets"


@dataclass(frozen=True, slots=True)
class GoogleSheetsSettings:
    api_key: str | None
    spreadsheet_id: str | None
    matches_range: str
    top_scorers_range: str | None
    base_url: str = GOOGLE_SHEETS_BASE_URL

    @classmethod
    def from_environment(cls) -> GoogleSheetsSettings:
        api_key = _read_env("GOOGLE_SHEETS_API_KEY")
        spreadsheet_id = _read_env("GOOGLE_SHEETS_SPREADSHEET_ID")
        matches_range = _read_env("GOOGLE_SHEETS_MATCHES_RANGE") or "Matches!A:Z"
        top_scorers_range = _read_env("GOOGLE_SHEETS_TOP_SCORERS_RANGE")
        base_url = _read_env("GOOGLE_SHEETS_BASE_URL") or GOOGLE_SHEETS_BASE_URL
        return cls(
            api_key=api_key,
            spreadsheet_id=spreadsheet_id,
            matches_range=matches_range,
            top_scorers_range=top_scorers_range,
            base_url=base_url.rstrip("/"),
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.spreadsheet_id)


@dataclass(frozen=True, slots=True)
class SheetTable:
    headers: tuple[str, ...]
    rows: tuple[dict[str, str], ...] = field(default_factory=tuple)


class GoogleSheetsClient:
    def __init__(
        self,
        *,
        settings: GoogleSheetsSettings | None = None,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings or GoogleSheetsSettings.from_environment()
        self._timeout = timeout
        self._client = client

    @property
    def provider(self) -> SyncProvider:
        return SyncProvider.GOOGLE_SHEETS

    @property
    def configured(self) -> bool:
        return self._settings.configured

    def fetch_match_batch(
        self,
        *,
        fixture_ids: Sequence[str] | None = None,
        include_top_scorers: bool = False,
    ) -> ProviderSyncBatch:
        self._ensure_configured()
        fetched_at = datetime.now(timezone.utc)
        table = self._fetch_table(self._settings.matches_range)
        matches = tuple(
            self._map_match_row(row)
            for row in table.rows
            if self._include_fixture_row(row=row, fixture_ids=fixture_ids)
        )
        top_scorers: tuple[ProviderTopScorer, ...] = ()
        if include_top_scorers and self._settings.top_scorers_range is not None:
            top_scorers = self.fetch_top_scorers()
        return ProviderSyncBatch(
            provider=self.provider,
            fetched_at=fetched_at,
            matches=matches,
            top_scorers=top_scorers,
            metadata={
                "spreadsheet_id": self._settings.spreadsheet_id,
                "matches_range": self._settings.matches_range,
                "top_scorers_range": self._settings.top_scorers_range,
                "requested_fixture_ids": list(fixture_ids or ()),
            },
        )

    def fetch_top_scorers(self) -> tuple[ProviderTopScorer, ...]:
        self._ensure_configured()
        if self._settings.top_scorers_range is None:
            return ()
        table = self._fetch_table(self._settings.top_scorers_range)
        return tuple(self._map_top_scorer_row(row) for row in table.rows)

    def _fetch_table(self, range_name: str) -> SheetTable:
        payload = self._request_json(range_name)
        raw_values = payload.get("values")
        if not isinstance(raw_values, list) or len(raw_values) == 0:
            return SheetTable(headers=(), rows=())
        normalized_rows = [self._normalize_row_values(row) for row in raw_values]
        headers = tuple(self._normalize_header(value) for value in normalized_rows[0])
        rows: list[dict[str, str]] = []
        for raw_row in normalized_rows[1:]:
            row_payload = {
                header: raw_row[index] if index < len(raw_row) else ""
                for index, header in enumerate(headers)
            }
            if any(value.strip() != "" for value in row_payload.values()):
                rows.append(row_payload)
        return SheetTable(headers=headers, rows=tuple(rows))

    def _map_match_row(self, row: Mapping[str, str]) -> ProviderMatchRecord:
        external_id = self._require_value(row, ("external_id", "fixture_id"))
        starts_at_raw = self._require_value(row, ("starts_at", "fixture_date"))
        status = self._require_value(row, ("status",))
        phase_raw = self._require_value(row, ("phase", "round"))
        home_team_name = self._require_value(row, ("home_team_name",))
        away_team_name = self._require_value(row, ("away_team_name",))
        home_code = self._optional_upper(row, ("home_team_fifa_code", "home_code"))
        away_code = self._optional_upper(row, ("away_team_fifa_code", "away_code"))
        involves_brazil = self._optional_bool(row, ("involves_brazil",))
        if involves_brazil is None:
            involves_brazil = "BRA" in {value for value in (home_code, away_code) if value is not None}
        return ProviderMatchRecord(
            provider=self.provider,
            external_id=external_id,
            starts_at=parse_timestamp(starts_at_raw),
            status=status,
            phase=parse_competition_phase(phase_raw),
            stage_round=self._optional_int(row, ("stage_round",)) or parse_stage_round(phase_raw),
            group_name=self._optional_upper(row, ("group_name",)),
            bracket_slot=self._optional_upper(row, ("bracket_slot",)),
            venue=self._optional_value(row, ("venue",)),
            home_team_name=home_team_name,
            away_team_name=away_team_name,
            home_team_fifa_code=home_code,
            away_team_fifa_code=away_code,
            involves_brazil=involves_brazil,
            official_home_goals=self._optional_int(row, ("official_home_goals", "home_goals")),
            official_away_goals=self._optional_int(row, ("official_away_goals", "away_goals")),
            winner_team_name=self._optional_value(row, ("winner_team_name",)),
            source_payload=dict(row),
        )

    def _map_top_scorer_row(self, row: Mapping[str, str]) -> ProviderTopScorer:
        return ProviderTopScorer(
            provider=self.provider,
            player_key=self._require_value(row, ("player_key", "player_id")),
            player_name=self._require_value(row, ("player_name",)),
            team_name=self._optional_value(row, ("team_name",)),
            goals=self._optional_int(row, ("goals",)) or 0,
            assists=self._optional_int(row, ("assists",)) or 0,
            source_payload=dict(row),
        )

    def _request_json(self, range_name: str) -> dict[str, Any]:
        response = self._perform_request(
            f"{self._settings.base_url}/{self._settings.spreadsheet_id}/values/{range_name}",
            params={"key": self._settings.api_key or ""},
        )
        if response.status_code >= 400:
            raise ProviderResponseError(f"Google Sheets request failed with status {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ProviderResponseError("Google Sheets response must be a JSON object")
        return payload

    def _perform_request(self, url: str, *, params: Mapping[str, str]) -> httpx.Response:
        if self._client is not None:
            return self._client.get(url, params=params, timeout=self._timeout)
        with httpx.Client() as client:
            return client.get(url, params=params, timeout=self._timeout)

    def _include_fixture_row(self, *, row: Mapping[str, str], fixture_ids: Sequence[str] | None) -> bool:
        if fixture_ids is None:
            return True
        fixture_id = self._optional_value(row, ("external_id", "fixture_id"))
        return fixture_id in set(fixture_ids) if fixture_id is not None else False

    def _ensure_configured(self) -> None:
        if not self.configured:
            raise ProviderConfigurationError("Google Sheets client is not configured")

    def _normalize_header(self, value: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().casefold())
        return normalized.strip("_")

    def _normalize_row_values(self, row: Any) -> list[str]:
        if not isinstance(row, list):
            return []
        values: list[str] = []
        for item in row:
            if item is None:
                values.append("")
            elif isinstance(item, str):
                values.append(item.strip())
            else:
                values.append(str(item).strip())
        return values

    def _require_value(self, row: Mapping[str, str], aliases: Sequence[str]) -> str:
        value = self._optional_value(row, aliases)
        if value is None:
            raise ProviderResponseError(
                f"Google Sheets row is missing required fields: {', '.join(aliases)}"
            )
        return value

    def _optional_value(self, row: Mapping[str, str], aliases: Sequence[str]) -> str | None:
        for alias in aliases:
            value = row.get(alias)
            if value is not None and value.strip() != "":
                return value.strip()
        return None

    def _optional_upper(self, row: Mapping[str, str], aliases: Sequence[str]) -> str | None:
        value = self._optional_value(row, aliases)
        return value.upper() if value is not None else None

    def _optional_int(self, row: Mapping[str, str], aliases: Sequence[str]) -> int | None:
        value = self._optional_value(row, aliases)
        return int(value) if value is not None else None

    def _optional_bool(self, row: Mapping[str, str], aliases: Sequence[str]) -> bool | None:
        value = self._optional_value(row, aliases)
        if value is None:
            return None
        normalized = value.casefold()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
        return None


def _read_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
