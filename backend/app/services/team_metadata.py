from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parents[2] / "data")))

CODE_ALIASES = {
    "SAU": "KSA",
}

REGIONAL_FLAGS = {
    "GB-ENG": "🏴",
    "GB-SCT": "🏴",
}


@dataclass(frozen=True, slots=True)
class TeamMetadata:
    code: str
    name: str
    iso2: str | None
    flag: str
    group: str | None


def iso2_to_flag(iso2: str | None) -> str:
    if not iso2:
        return "🏳"
    normalized = iso2.strip().upper()
    if normalized in REGIONAL_FLAGS:
        return REGIONAL_FLAGS[normalized]
    if len(normalized) != 2 or not normalized.isalpha():
        return "🏳"
    return "".join(chr(ord(char) + 127397) for char in normalized)


def normalize_team_code(value: str | None) -> str | None:
    if value is None:
        return None
    code = value.strip().upper()
    if not code or code == "TBD":
        return None
    return CODE_ALIASES.get(code, code)


@lru_cache(maxsize=1)
def get_team_metadata_by_code() -> dict[str, TeamMetadata]:
    path = DATA_DIR / "teams-groups.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: dict[str, TeamMetadata] = {}
    for item in payload.get("teams", []):
        if not isinstance(item, dict):
            continue
        code = normalize_team_code(_optional_string(item.get("code")))
        name = _optional_string(item.get("name"))
        if code is None or name is None:
            continue
        iso2 = _optional_string(item.get("iso2"))
        rows[code] = TeamMetadata(
            code=code,
            name=name,
            iso2=iso2,
            flag=iso2_to_flag(iso2),
            group=_optional_string(item.get("group")),
        )
    return rows


def get_team_metadata(code: str | None, fallback_name: str | None = None) -> TeamMetadata:
    normalized = normalize_team_code(code)
    if normalized is not None:
        team = get_team_metadata_by_code().get(normalized)
        if team is not None:
            return team
    fallback = (fallback_name or code or "TBD").strip() or "TBD"
    return TeamMetadata(
        code=normalized or fallback,
        name=fallback,
        iso2=None,
        flag="🏳",
        group=None,
    )


@lru_cache(maxsize=1)
def get_players_by_id() -> dict[str, dict[str, Any]]:
    path = DATA_DIR / "players-attackers.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: dict[str, dict[str, Any]] = {}
    for item in payload.get("players", []):
        if not isinstance(item, dict):
            continue
        player_id = _optional_string(item.get("id"))
        if player_id:
            rows[player_id] = item
    return rows


def _optional_string(value: object) -> str | None:
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return None
