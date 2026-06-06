"""Seed routine: inserts initial data from JSON files on first startup.

Idempotent — checks for existing SEED-sourced records before inserting.
Run order: group-stage matches → knockout matches.
Players are served at runtime from the JSON file, not stored in DB.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.schema import CompetitionPhase, CompetitionPhaseConfig, Match, ScoringRule, SyncProvider
from app.repositories.queries import get_session_local

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"

_PHASE_MAP: dict[str, CompetitionPhase] = {
    "GROUP_STAGE": CompetitionPhase.GROUP_STAGE,
    "ROUND_OF_32": CompetitionPhase.ROUND_OF_32,
    "ROUND_OF_16": CompetitionPhase.ROUND_OF_16,
    "QUARTER_FINAL": CompetitionPhase.QUARTER_FINAL,
    "SEMI_FINAL": CompetitionPhase.SEMI_FINAL,
    "THIRD_PLACE": CompetitionPhase.THIRD_PLACE,
    "FINAL": CompetitionPhase.FINAL,
}

_PHASE_SCHEDULES: list[tuple[str, str, CompetitionPhase | None, int | None, int, str]] = [
    (
        "initial_predictions",
        "Palpites iniciais",
        None,
        None,
        0,
        "2026-06-11T16:00:00-03:00",
    ),
    ("round1", "Fase de grupos · Rodada 1", CompetitionPhase.GROUP_STAGE, 1, 1, "2026-06-11T16:00:00-03:00"),
    ("round2", "Fase de grupos · Rodada 2", CompetitionPhase.GROUP_STAGE, 2, 2, "2026-06-18T13:00:00-03:00"),
    ("round3", "Fase de grupos · Rodada 3", CompetitionPhase.GROUP_STAGE, 3, 3, "2026-06-24T16:00:00-03:00"),
    ("roundOf32", "16 avos", CompetitionPhase.ROUND_OF_32, None, 4, "2026-06-28T16:00:00-03:00"),
    ("roundOf16", "Oitavas", CompetitionPhase.ROUND_OF_16, None, 5, "2026-07-04T14:00:00-03:00"),
    ("quarterFinal", "Quartas", CompetitionPhase.QUARTER_FINAL, None, 6, "2026-07-09T17:00:00-03:00"),
    ("semiFinal", "Semifinal", CompetitionPhase.SEMI_FINAL, None, 7, "2026-07-14T16:00:00-03:00"),
    ("final", "Final", CompetitionPhase.FINAL, None, 8, "2026-07-19T16:00:00-03:00"),
]


def _already_seeded(session: Session) -> bool:
    count = session.query(Match).filter(Match.external_provider == SyncProvider.SEED).count()
    return count > 0


def _parse_dt(value: str | None) -> datetime:
    if not value:
        return datetime(2026, 6, 11, 12, 0, 0, tzinfo=timezone.utc)
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _seed_phase_configs(session: Session) -> int:
    inserted = 0
    for phase_key, label, phase, stage_round, sort_order, starts_at in _PHASE_SCHEDULES:
        existing = session.scalar(
            select(CompetitionPhaseConfig).where(CompetitionPhaseConfig.phase_key == phase_key)
        )
        if existing is not None:
            continue
        first_match_starts_at = _parse_dt(starts_at)
        lock_at = first_match_starts_at - timedelta(minutes=30)
        config = CompetitionPhaseConfig(
            phase_key=phase_key,
            label=label,
            phase=phase,
            stage_round=stage_round,
            sort_order=sort_order,
            first_match_starts_at=first_match_starts_at,
            lock_at=lock_at,
            explore_at=lock_at,
            is_force_locked=False,
            is_active=True,
        )
        session.add(config)
        inserted += 1
    return inserted


def _seed_scoring_rules(session: Session) -> int:
    existing = session.scalar(select(ScoringRule).where(ScoringRule.name == "default"))
    if existing is not None:
        return 0
    session.add(
        ScoringRule(
            name="default",
            exact_points=3,
            result_points=1,
            brazil_multiplier=2,
            champion_points=10,
            top_scorer_points=15,
            is_active=True,
        )
    )
    return 1


def _seed_group_stage(session: Session) -> int:
    path = DATA_DIR / "group-stage-matches.json"
    if not path.exists():
        logger.warning("group-stage-matches.json not found at %s", path)
        return 0

    with path.open() as f:
        data = json.load(f)

    teams_path = DATA_DIR / "teams-groups.json"
    brazil_codes: set[str] = set()
    if teams_path.exists():
        with teams_path.open() as tf:
            td = json.load(tf)
        brazil_codes = {t["code"] for t in td.get("teams", []) if t.get("isSpecialMultiplierTeam")}

    inserted = 0
    for m in data.get("matches", []):
        home = m.get("homeTeam", "")
        away = m.get("awayTeam", "")
        involves_brazil = home in brazil_codes or away in brazil_codes
        match = Match(
            external_provider=SyncProvider.SEED,
            external_id=str(m["id"]),
            phase=CompetitionPhase.GROUP_STAGE,
            stage_round=m.get("round"),
            group_name=m.get("group"),
            starts_at=_parse_dt(m.get("startsAt")),
            venue=m.get("venue"),
            home_team_name=home,
            away_team_name=away,
            home_team_fifa_code=home,
            away_team_fifa_code=away,
            involves_brazil=involves_brazil,
            status="SCHEDULED",
        )
        session.add(match)
        inserted += 1
    return inserted


def _seed_knockout(session: Session) -> int:
    path = DATA_DIR / "bracket-knockout.json"
    if not path.exists():
        logger.warning("bracket-knockout.json not found at %s", path)
        return 0

    with path.open() as f:
        data = json.load(f)

    phase_keys = [
        ("roundOf32", CompetitionPhase.ROUND_OF_32),
        ("roundOf16", CompetitionPhase.ROUND_OF_16),
        ("quarterFinals", CompetitionPhase.QUARTER_FINAL),
        ("semiFinals", CompetitionPhase.SEMI_FINAL),
        ("thirdPlace", CompetitionPhase.THIRD_PLACE),
        ("final", CompetitionPhase.FINAL),
    ]

    inserted = 0
    for key, phase in phase_keys:
        raw = data.get(key, [])
        if isinstance(raw, dict):
            raw = [raw]
        for m in raw:
            match = Match(
                external_provider=SyncProvider.SEED,
                external_id=str(m["id"]),
                phase=phase,
                bracket_slot=m.get("slot"),
                feeder_home_key=m.get("homeFeeder"),
                feeder_away_key=m.get("awayFeeder"),
                starts_at=_parse_dt(m.get("startsAt")),
                venue=m.get("venue"),
                home_team_name=m.get("homeTeam") or "TBD",
                away_team_name=m.get("awayTeam") or "TBD",
                status="SCHEDULED",
                involves_brazil=False,
            )
            session.add(match)
            inserted += 1
    return inserted


def run_seed() -> None:
    session_factory = get_session_local()
    with session_factory() as session:
        logger.info("Running initial data seed...")
        try:
            gs = 0
            ko = 0
            if not _already_seeded(session):
                gs = _seed_group_stage(session)
                ko = _seed_knockout(session)
            phase_configs = _seed_phase_configs(session)
            scoring_rules = _seed_scoring_rules(session)
            session.commit()
            logger.info(
                "Seed complete: %d group-stage + %d knockout matches inserted; %d phase configs + %d scoring rows ensured.",
                gs,
                ko,
                phase_configs,
                scoring_rules,
            )
        except Exception:
            session.rollback()
            logger.exception("Seed failed — rolled back.")
            raise


def main() -> None:
    run_seed()


if __name__ == "__main__":
    main()
