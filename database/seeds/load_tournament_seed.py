from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.schema import CompetitionPhase, CompetitionWindow, Match, SyncProvider
from app.repositories.queries import get_session_local


@dataclass(frozen=True, slots=True)
class TeamSeed:
    code: str
    name: str
    group_name: str
    multiplier_value: int


@dataclass(frozen=True, slots=True)
class SeedStats:
    teams: int
    group_stage_matches: int
    knockout_matches: int
    inserted_matches: int
    updated_matches: int


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_seed_datetime(value: Any, fallback: datetime) -> datetime:
    if isinstance(value, str) and value.strip() != "":
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        return datetime.fromisoformat(normalized)
    return fallback


def load_team_seeds(repo_root: Path) -> dict[str, TeamSeed]:
    payload = read_json(repo_root / "data" / "teams-groups.json")
    teams_raw = payload.get("teams", [])
    teams: dict[str, TeamSeed] = {}
    for team in teams_raw:
        if not isinstance(team, Mapping):
            continue
        code = str(team["code"])
        teams[code] = TeamSeed(
            code=code,
            name=str(team["name"]),
            group_name=str(team["group"]),
            multiplier_value=int(team.get("multiplierValue", 1)),
        )
    if len(teams) != 48:
        raise ValueError(f"expected 48 teams, got {len(teams)}")
    return teams


def ensure_competition_window(db_session: Session) -> None:
    settings = get_settings()
    existing = db_session.scalar(
        select(CompetitionWindow).where(CompetitionWindow.name == "default")
    )
    if existing is None:
        db_session.add(
            CompetitionWindow(
                name="default",
                prediction_close_at=settings.competition.prediction_close_at,
                explore_release_at=settings.competition.explore_release_at,
                is_active=True,
            )
        )


def upsert_match(db_session: Session, *, external_id: str, defaults: dict[str, Any]) -> tuple[Match, bool]:
    match = db_session.scalar(
        select(Match).where(
            Match.external_provider == SyncProvider.SEED,
            Match.external_id == external_id,
        )
    )
    created = False
    if match is None:
        match = Match(external_provider=SyncProvider.SEED, external_id=external_id, **defaults)
        db_session.add(match)
        created = True
    else:
        for key, value in defaults.items():
            setattr(match, key, value)
        db_session.add(match)
    return match, created


def seed_group_stage_matches(db_session: Session, repo_root: Path, teams: Mapping[str, TeamSeed]) -> tuple[int, int, int]:
    payload = read_json(repo_root / "data" / "group-stage-matches.json")
    matches_raw = payload.get("matches", [])
    if len(matches_raw) != 72:
        raise ValueError(f"expected 72 group-stage matches, got {len(matches_raw)}")
    inserted = 0
    updated = 0
    for row in matches_raw:
        if not isinstance(row, Mapping):
            continue
        home_code = str(row["homeTeam"])
        away_code = str(row["awayTeam"])
        home_team = teams[home_code]
        away_team = teams[away_code]
        external_id = f"seed-group-{row['id']}"
        defaults = {
            "phase": CompetitionPhase.GROUP_STAGE,
            "stage_round": int(row["round"]),
            "group_name": str(row["group"]),
            "starts_at": parse_seed_datetime(
                row.get("startsAt"),
                get_settings().competition.prediction_close_at,
            ),
            "venue": row["venue"],
            "home_team_name": home_team.name,
            "away_team_name": away_team.name,
            "home_team_fifa_code": home_team.code,
            "away_team_fifa_code": away_team.code,
            "involves_brazil": home_code == "BRA" or away_code == "BRA",
            "status": "SCHEDULED",
            "source_payload": dict(row),
        }
        match, created = upsert_match(db_session, external_id=external_id, defaults=defaults)
        inserted += 1 if created else 0
        updated += 0 if created else 1
        db_session.add(match)
    return len(matches_raw), inserted, updated


def _iter_knockout_rows(payload: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    sections = {
        "roundOf32": CompetitionPhase.ROUND_OF_32,
        "roundOf16": CompetitionPhase.ROUND_OF_16,
        "quarterFinals": CompetitionPhase.QUARTER_FINAL,
        "semiFinals": CompetitionPhase.SEMI_FINAL,
        "thirdPlace": CompetitionPhase.THIRD_PLACE,
        "final": CompetitionPhase.FINAL,
    }
    for section_name in sections:
        rows = payload.get(section_name, [])
        for row in rows:
            if isinstance(row, Mapping):
                yield section_name, row


def seed_knockout_matches(db_session: Session, repo_root: Path) -> tuple[int, int, int]:
    payload = read_json(repo_root / "data" / "bracket-knockout.json")
    rows = list(_iter_knockout_rows(payload))
    if len(rows) != 32:
        raise ValueError(f"expected 32 knockout matches, got {len(rows)}")
    phase_map = {
        "roundOf32": CompetitionPhase.ROUND_OF_32,
        "roundOf16": CompetitionPhase.ROUND_OF_16,
        "quarterFinals": CompetitionPhase.QUARTER_FINAL,
        "semiFinals": CompetitionPhase.SEMI_FINAL,
        "thirdPlace": CompetitionPhase.THIRD_PLACE,
        "final": CompetitionPhase.FINAL,
    }
    inserted = 0
    updated = 0
    for section_name, row in rows:
        external_id = f"seed-knockout-{row['id']}"
        defaults = {
            "phase": phase_map[section_name],
            "stage_round": None,
            "group_name": None,
            "bracket_slot": str(row["slot"]),
            "feeder_home_key": row.get("homeFeeder"),
            "feeder_away_key": row.get("awayFeeder"),
            "starts_at": parse_seed_datetime(
                row.get("startsAt"),
                get_settings().competition.explore_release_at,
            ),
            "venue": row.get("venue"),
            "home_team_name": row.get("homeTeam") or "TBD",
            "away_team_name": row.get("awayTeam") or "TBD",
            "home_team_fifa_code": row.get("homeTeam"),
            "away_team_fifa_code": row.get("awayTeam"),
            "involves_brazil": False,
            "status": "SCHEDULED",
            "source_payload": dict(row),
        }
        match, created = upsert_match(db_session, external_id=external_id, defaults=defaults)
        inserted += 1 if created else 0
        updated += 0 if created else 1
        db_session.add(match)
    return len(rows), inserted, updated


def run_seed(db_session: Session | None = None) -> SeedStats:
    repo_root = get_repo_root()
    teams = load_team_seeds(repo_root)
    own_session = db_session is None
    session = db_session or get_session_local()()
    try:
        ensure_competition_window(session)
        group_count, group_inserted, group_updated = seed_group_stage_matches(session, repo_root, teams)
        knockout_count, knockout_inserted, knockout_updated = seed_knockout_matches(session, repo_root)
        if own_session:
            session.commit()
        return SeedStats(
            teams=len(teams),
            group_stage_matches=group_count,
            knockout_matches=knockout_count,
            inserted_matches=group_inserted + knockout_inserted,
            updated_matches=group_updated + knockout_updated,
        )
    except Exception:
        if own_session:
            session.rollback()
        raise
    finally:
        if own_session:
            session.close()


def main() -> None:
    stats = run_seed()
    print(
        json.dumps(
            {
                "teams": stats.teams,
                "group_stage_matches": stats.group_stage_matches,
                "knockout_matches": stats.knockout_matches,
                "inserted_matches": stats.inserted_matches,
                "updated_matches": stats.updated_matches,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
