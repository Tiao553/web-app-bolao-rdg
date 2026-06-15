from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from app.services.match_status import is_terminal_match_status
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
    "finished": "FINISHED",
}


@dataclass(frozen=True, slots=True)
class TheSportsDBEventResult:
    event_id: str
    starts_at: datetime
    date: str | None
    time: str | None
    round: int
    stage: str | None
    status: str
    home_name: str
    home_code: str
    away_name: str
    away_code: str
    home_goals: int | None
    away_goals: int | None
    league_id: str | None
    league_name: str | None
    league_season: str | None
    source_payload: dict[str, Any]

    @property
    def terminal(self) -> bool:
        return is_terminal_match_status(self.status)


def normalize_event_row(row: Mapping[str, Any]) -> TheSportsDBEventResult | None:
    event_id = _require_str(row.get("idEvent"), "idEvent")
    home_name = _require_str(row.get("strHomeTeam"), "strHomeTeam")
    away_name = _require_str(row.get("strAwayTeam"), "strAwayTeam")
    home_code = _provider_name_to_code(home_name)
    away_code = _provider_name_to_code(away_name)
    if home_code is None or away_code is None:
        return None

    home_team = get_team_metadata(home_code)
    away_team = get_team_metadata(away_code)
    if home_team.group is None or away_team.group is None or home_team.group != away_team.group:
        return None

    round_number = _optional_int(row.get("intRound"))
    if round_number not in {1, 2, 3}:
        return None

    timestamp = _require_str(row.get("strTimestamp"), "strTimestamp")
    starts_at = _parse_timestamp(timestamp)
    status = normalize_status(row.get("strStatus"))
    return TheSportsDBEventResult(
        event_id=event_id,
        starts_at=starts_at,
        date=_optional_str(row.get("dateEvent")),
        time=_optional_str(row.get("strTime")),
        round=round_number,
        stage=_optional_str(row.get("strStage")),
        status=status,
        home_name=home_team.name,
        home_code=home_team.code,
        away_name=away_team.name,
        away_code=away_team.code,
        home_goals=_optional_int(row.get("intHomeScore")),
        away_goals=_optional_int(row.get("intAwayScore")),
        league_id=_optional_str(row.get("idLeague")),
        league_name=_optional_str(row.get("strLeague")),
        league_season=_optional_str(row.get("strSeason")),
        source_payload=dict(row),
    )


def build_result_payload(result: TheSportsDBEventResult) -> dict[str, Any]:
    home_team = get_team_metadata(result.home_code, result.home_name)
    away_team = get_team_metadata(result.away_code, result.away_name)
    winner = _build_winner_payload(
        home_name=home_team.name,
        away_name=away_team.name,
        home_code=home_team.code,
        away_code=away_team.code,
        home_goals=result.home_goals,
        away_goals=result.away_goals,
    )
    return {
        "event_id": result.event_id,
        "date": result.date,
        "time": result.time,
        "round": str(result.round),
        "stage": result.stage,
        "status": result.status,
        "home": {
            "id": result.source_payload.get("idHomeTeam"),
            "name": home_team.name,
            "tag": home_team.code,
            "goals": result.home_goals,
        },
        "away": {
            "id": result.source_payload.get("idAwayTeam"),
            "name": away_team.name,
            "tag": away_team.code,
            "goals": result.away_goals,
        },
        "result": {
            "home_goals": result.home_goals,
            "away_goals": result.away_goals,
            "score": (
                f"{result.home_goals}x{result.away_goals}"
                if result.home_goals is not None and result.away_goals is not None
                else None
            ),
            "winner": winner,
        },
        "league": {
            "id": result.league_id,
            "name": result.league_name,
            "season": result.league_season,
        },
    }


def list_recent_result_payloads(
    rows: Sequence[Mapping[str, Any]],
    *,
    limit: int = 15,
) -> list[dict[str, Any]]:
    results = [normalize_event_row(row) for row in rows]
    filtered = [result for result in results if result is not None and result.terminal]
    filtered.sort(key=lambda result: (result.starts_at, result.event_id), reverse=True)
    return [build_result_payload(result) for result in filtered[:limit]]


def _build_winner_payload(
    *,
    home_name: str,
    away_name: str,
    home_code: str,
    away_code: str,
    home_goals: int | None,
    away_goals: int | None,
) -> dict[str, str | None]:
    if home_goals is None or away_goals is None:
        return {"name": None, "tag": None}
    if home_goals > away_goals:
        return {"name": home_name, "tag": home_code}
    if away_goals > home_goals:
        return {"name": away_name, "tag": away_code}
    return {"name": "Draw", "tag": "DRAW"}


def normalize_status(value: Any) -> str:
    raw = _optional_str(value)
    if raw is None:
        return "UNKNOWN"
    return THE_SPORTS_DB_STATUS_MAP.get(raw.casefold(), raw.strip().upper())


def _provider_name_to_code(name: str) -> str | None:
    normalized = name.strip().casefold()
    return THE_SPORTS_DB_TEAM_ALIASES.get(normalized)


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.strip())
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _require_str(value: Any, field_name: str) -> str:
    normalized = _optional_str(value)
    if normalized is None:
        raise ValueError(f"TheSportsDB field '{field_name}' must be a non-empty string")
    return normalized


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    if isinstance(value, int):
        return str(value)
    return None


def _optional_int(value: Any) -> int | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    return None
