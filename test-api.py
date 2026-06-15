from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime
from typing import Any

import requests

THE_SPORTS_DB_BASE_URL = "https://www.thesportsdb.com/api/v1/json/123"
THE_SPORTS_DB_LEAGUE_ID = "4429"

TERMINAL_STATUSES = {
    "FT",
    "AET",
    "PEN",
    "FINISHED",
}


def fetch_world_cup_events(*, season: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{THE_SPORTS_DB_BASE_URL}/eventsseason.php",
        params={
            "id": THE_SPORTS_DB_LEAGUE_ID,
            "s": season,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    events = payload.get("events") or []
    return [event for event in events if isinstance(event, dict)]


def build_recent_results(events: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    finished_events = [event for event in events if normalize_status(event.get("strStatus")) in TERMINAL_STATUSES]
    finished_events.sort(key=event_sort_key, reverse=True)
    return [format_event(event) for event in finished_events[:limit]]


def format_event(event: dict[str, Any]) -> dict[str, Any]:
    home_name = str(event.get("strHomeTeam") or "").strip()
    away_name = str(event.get("strAwayTeam") or "").strip()
    home_goals = optional_int(event.get("intHomeScore"))
    away_goals = optional_int(event.get("intAwayScore"))

    return {
        "event_id": str(event.get("idEvent") or ""),
        "date": optional_str(event.get("dateEvent")),
        "time": optional_str(event.get("strTime")),
        "round": optional_str(event.get("intRound")),
        "stage": optional_str(event.get("strStage")),
        "status": normalize_status(event.get("strStatus")),
        "home": {
            "id": optional_str(event.get("idHomeTeam")),
            "name": home_name or None,
            "tag": derive_tag(home_name),
            "goals": home_goals,
        },
        "away": {
            "id": optional_str(event.get("idAwayTeam")),
            "name": away_name or None,
            "tag": derive_tag(away_name),
            "goals": away_goals,
        },
        "result": {
            "home_goals": home_goals,
            "away_goals": away_goals,
            "score": f"{home_goals}x{away_goals}" if home_goals is not None and away_goals is not None else None,
            "winner": build_winner(home_name=home_name, away_name=away_name, home_goals=home_goals, away_goals=away_goals),
        },
        "league": {
            "id": optional_str(event.get("idLeague")),
            "name": optional_str(event.get("strLeague")),
            "season": optional_str(event.get("strSeason")),
        },
    }


def build_winner(
    *,
    home_name: str,
    away_name: str,
    home_goals: int | None,
    away_goals: int | None,
) -> dict[str, str | None]:
    if home_goals is None or away_goals is None:
        return {"name": None, "tag": None}
    if home_goals > away_goals:
        return {"name": home_name or None, "tag": derive_tag(home_name)}
    if away_goals > home_goals:
        return {"name": away_name or None, "tag": derive_tag(away_name)}
    return {"name": "Draw", "tag": "DRAW"}


def derive_tag(value: str) -> str | None:
    normalized = unicodedata.normalize("NFKD", value)
    letters = re.sub(r"[^A-Za-z]", "", normalized).upper()
    return letters[:3] or None


def event_sort_key(event: dict[str, Any]) -> datetime:
    date_value = optional_str(event.get("dateEvent")) or "1970-01-01"
    time_value = optional_str(event.get("strTime")) or "00:00:00"
    return datetime.fromisoformat(f"{date_value}T{time_value}")


def normalize_status(value: Any) -> str:
    normalized = optional_str(value)
    if normalized is None:
        return "UNKNOWN"
    return normalized.upper()


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    if isinstance(value, int):
        return str(value)
    return None


def optional_int(value: Any) -> int | None:
    text = optional_str(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print the latest finished TheSportsDB results.")
    parser.add_argument("--season", default="2026", help="Season to fetch, defaults to 2026.")
    parser.add_argument("--limit", type=int, default=15, help="Maximum number of finished results to print.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    events = fetch_world_cup_events(season=args.season)
    results = build_recent_results(events, limit=args.limit)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
