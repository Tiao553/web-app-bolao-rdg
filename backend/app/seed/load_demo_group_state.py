from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.schema import (
    AccessStatus,
    CompetitionPhase,
    CompetitionPhaseConfig,
    CompetitionPrediction,
    CompetitionWindow,
    Match,
    MatchPrediction,
    PredictionType,
    User,
)
from app.repositories.queries import get_session_local
from app.domain.bracket import QualifiedThirdPlaceTeam, allocate_third_place_slots
from app.services.recalculation_service import recalculate_competition_state


@dataclass(frozen=True, slots=True)
class DemoUser:
    id: object
    email: str
    full_name: str


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_group_order() -> dict[str, list[str]]:
    payload = load_json(get_repo_root() / "data" / "teams-groups.json")
    groups: dict[str, list[str]] = defaultdict(list)
    for team in payload.get("teams", []):
        groups[str(team["group"])].append(str(team["code"]))
    return dict(groups)


def load_team_lookup() -> dict[str, str]:
    payload = load_json(get_repo_root() / "data" / "teams-groups.json")
    return {
        str(team["code"]): str(team["name"])
        for team in payload.get("teams", [])
        if isinstance(team, dict)
    }


def load_knockout_payload() -> dict:
    return load_json(get_repo_root() / "data" / "bracket-knockout.json")


def load_top_scorer_choices() -> list[tuple[str, str]]:
    payload = load_json(get_repo_root() / "data" / "players-attackers.json")
    choices: list[tuple[str, str]] = []
    for player in payload.get("players", []):
        player_id = player.get("id")
        player_name = player.get("name")
        if isinstance(player_id, str) and isinstance(player_name, str):
            choices.append((player_id, player_name))
        if len(choices) >= 2:
            break
    if len(choices) < 2:
        raise ValueError("expected at least two players in players-attackers.json")
    return choices


def build_official_score(home_rank: int, away_rank: int) -> tuple[int, int]:
    if home_rank < away_rank:
        gap = away_rank - home_rank
        return (3, 0) if gap >= 2 else (2, 1)
    gap = home_rank - away_rank
    return (0, 3) if gap >= 2 else (1, 2)


def build_user_one_prediction(match_index: int, home: int, away: int) -> tuple[int, int]:
    pattern = match_index % 4
    if pattern == 0:
        return home, away
    if home > away:
        return max(home - 1, 0), away
    if away > home:
        return home, max(away - 1, 0)
    return home + 1, away


def build_user_two_prediction(match_index: int, home: int, away: int) -> tuple[int, int]:
    pattern = match_index % 5
    if pattern == 0:
        return home, away
    if pattern == 1:
        return away, home
    if pattern == 2:
        return 1, 1
    if home > away:
        return home, away + 1
    return home + 1, away


def ensure_released_window(db_session: Session) -> None:
    now = datetime.now(timezone.utc)
    phase_configs = list(
        db_session.scalars(
            select(CompetitionPhaseConfig).where(CompetitionPhaseConfig.is_active.is_(True))
        ).all()
    )
    if phase_configs:
        for config in phase_configs:
            config.lock_at = now - timedelta(days=7)
            config.explore_at = now - timedelta(days=7)
            config.is_force_locked = False
            db_session.add(config)
    else:
        window = db_session.scalar(
            select(CompetitionWindow)
            .where(CompetitionWindow.is_active.is_(True))
            .order_by(CompetitionWindow.updated_at.desc(), CompetitionWindow.created_at.desc())
        )
        if window is None:
            window = CompetitionWindow(
                name="default",
                prediction_close_at=now - timedelta(days=7),
                explore_release_at=now - timedelta(days=6),
                is_active=True,
            )
        else:
            window.prediction_close_at = now - timedelta(days=7)
            window.explore_release_at = now - timedelta(days=6)
            window.is_active = True
        db_session.add(window)
    db_session.flush()


def get_demo_users(db_session: Session) -> tuple[DemoUser, DemoUser]:
    users = list(
        db_session.scalars(
            select(User)
            .where(
                User.access_status == AccessStatus.APPROVED,
                User.is_active.is_(True),
            )
            .order_by(User.created_at.asc(), User.id.asc())
            .limit(2)
        ).all()
    )
    if len(users) < 2:
        raise ValueError("need at least two approved active users in the docker database")
    return (
        DemoUser(id=users[0].id, email=users[0].email, full_name=users[0].full_name),
        DemoUser(id=users[1].id, email=users[1].email, full_name=users[1].full_name),
    )


def seed_group_stage_results_and_predictions(db_session: Session, users: tuple[DemoUser, DemoUser]) -> dict[str, int]:
    group_order = load_group_order()
    matches = list(
        db_session.scalars(
            select(Match)
            .where(Match.phase == CompetitionPhase.GROUP_STAGE)
            .order_by(Match.group_name.asc(), Match.stage_round.asc(), Match.starts_at.asc(), Match.id.asc())
        ).all()
    )
    if len(matches) != 72:
        raise ValueError(f"expected 72 group-stage matches, got {len(matches)}")

    user_ids = [users[0].id, users[1].id]
    match_ids = [match.id for match in matches]
    db_session.execute(
        delete(MatchPrediction).where(
            MatchPrediction.user_id.in_(user_ids),
            MatchPrediction.match_id.in_(match_ids),
        )
    )

    prediction_rows = 0
    finished_rows = 0
    for match_index, match in enumerate(matches):
        if match.group_name is None or match.home_team_fifa_code is None or match.away_team_fifa_code is None:
            raise ValueError(f"group-stage match {match.id} is missing group or team codes")
        rank_map = {team_code: idx for idx, team_code in enumerate(group_order[match.group_name])}
        home_rank = rank_map[match.home_team_fifa_code]
        away_rank = rank_map[match.away_team_fifa_code]
        official_home, official_away = build_official_score(home_rank, away_rank)

        match.status = "FT"
        match.official_home_goals = official_home
        match.official_away_goals = official_away
        match.winner_team_name = (
            match.home_team_name if official_home > official_away else match.away_team_name
        )
        match.has_manual_override = True
        match.synced_at = datetime.now(timezone.utc)
        source_payload = dict(match.source_payload or {})
        source_payload["demoSeed"] = "group-stage-results"
        match.source_payload = source_payload
        db_session.add(match)
        finished_rows += 1

        p1_home, p1_away = build_user_one_prediction(match_index, official_home, official_away)
        p2_home, p2_away = build_user_two_prediction(match_index, official_home, official_away)
        db_session.add(
            MatchPrediction(
                user_id=users[0].id,
                match_id=match.id,
                home_goals=p1_home,
                away_goals=p1_away,
            )
        )
        db_session.add(
            MatchPrediction(
                user_id=users[1].id,
                match_id=match.id,
                home_goals=p2_home,
                away_goals=p2_away,
            )
        )
        prediction_rows += 2

    db_session.flush()
    return {"finished_matches": finished_rows, "match_predictions": prediction_rows}


def seed_initial_predictions(db_session: Session, users: tuple[DemoUser, DemoUser]) -> dict[str, int]:
    db_session.execute(
        delete(CompetitionPrediction).where(CompetitionPrediction.user_id.in_([users[0].id, users[1].id]))
    )
    top_scorers = load_top_scorer_choices()
    rows = [
        CompetitionPrediction(
            user_id=users[0].id,
            prediction_type=PredictionType.CHAMPION,
            selection_key="BRA",
            selection_label="Brasil",
        ),
        CompetitionPrediction(
            user_id=users[1].id,
            prediction_type=PredictionType.CHAMPION,
            selection_key="FRA",
            selection_label="França",
        ),
        CompetitionPrediction(
            user_id=users[0].id,
            prediction_type=PredictionType.TOP_SCORER,
            selection_key=top_scorers[0][0],
            selection_label=top_scorers[0][1],
        ),
        CompetitionPrediction(
            user_id=users[1].id,
            prediction_type=PredictionType.TOP_SCORER,
            selection_key=top_scorers[1][0],
            selection_label=top_scorers[1][1],
        ),
    ]
    db_session.add_all(rows)
    db_session.flush()
    return {"competition_predictions": len(rows)}


def _resolve_slot_code(
    slot_definition: dict | None,
    *,
    group_order: dict[str, list[str]],
    third_place_by_slot: dict[str, str],
    bracket_slot: str,
) -> str | None:
    if not isinstance(slot_definition, dict):
        return None
    slot_type = slot_definition.get("type")
    group_name = slot_definition.get("group")
    if slot_type == "WINNER" and isinstance(group_name, str):
        return group_order[group_name][0]
    if slot_type == "RUNNER_UP" and isinstance(group_name, str):
        return group_order[group_name][1]
    if slot_type == "THIRD":
        return third_place_by_slot.get(bracket_slot)
    return None


def repair_knockout_bracket(db_session: Session) -> dict[str, int]:
    team_lookup = load_team_lookup()
    group_order = load_group_order()
    knockout_payload = load_knockout_payload()
    qualified_thirds = [
        QualifiedThirdPlaceTeam(group_name=group_name, team_key=teams[2])
        for group_name, teams in sorted(group_order.items())[:8]
    ]
    third_place_by_slot = {
        allocation.slot: allocation.team_key
        for allocation in allocate_third_place_slots(qualified_thirds)
    }
    matches_by_slot = {
        match.bracket_slot: match
        for match in db_session.scalars(
            select(Match).where(Match.bracket_slot.is_not(None))
        ).all()
        if match.bracket_slot is not None
    }

    updated = 0
    for row in knockout_payload.get("roundOf32", []):
        if not isinstance(row, dict):
            continue
        slot = str(row["slot"])
        match = matches_by_slot.get(slot)
        if match is None:
            continue
        home_code = _resolve_slot_code(
            row.get("homeSlot"),
            group_order=group_order,
            third_place_by_slot=third_place_by_slot,
            bracket_slot=slot,
        )
        away_code = _resolve_slot_code(
            row.get("awaySlot"),
            group_order=group_order,
            third_place_by_slot=third_place_by_slot,
            bracket_slot=slot,
        )
        home_slot = row.get("homeSlot") or {}
        away_slot = row.get("awaySlot") or {}
        match.feeder_home_key = (
            f"{home_slot['type']}:{home_slot['group']}"
            if isinstance(home_slot, dict) and home_slot.get("type") in {"WINNER", "RUNNER_UP"} and isinstance(home_slot.get("group"), str)
            else match.feeder_home_key
        )
        match.feeder_away_key = (
            f"{away_slot['type']}:{away_slot['group']}"
            if isinstance(away_slot, dict) and away_slot.get("type") in {"WINNER", "RUNNER_UP"} and isinstance(away_slot.get("group"), str)
            else match.feeder_away_key
        )
        if home_code is not None:
            match.home_team_fifa_code = home_code
            match.home_team_name = team_lookup[home_code]
        if away_code is not None:
            match.away_team_fifa_code = away_code
            match.away_team_name = team_lookup[away_code]
        db_session.add(match)
        updated += 1

    for section in ("roundOf16", "quarterFinals", "semiFinals", "thirdPlace", "final"):
        rows = knockout_payload.get(section, [])
        if isinstance(rows, dict):
            rows = [rows]
        for row in rows:
            if not isinstance(row, dict):
                continue
            slot = str(row["slot"])
            match = matches_by_slot.get(slot)
            if match is None:
                continue
            home_feeder = row.get("homeFeeder")
            away_feeder = row.get("awayFeeder")
            if isinstance(home_feeder, str):
                match.feeder_home_key = home_feeder
            if isinstance(away_feeder, str):
                match.feeder_away_key = away_feeder
            db_session.add(match)
            updated += 1

    db_session.flush()
    return {"knockout_slots_prepared": updated}


def run() -> dict[str, object]:
    session = get_session_local()()
    try:
        ensure_released_window(session)
        users = get_demo_users(session)
        summary = {}
        summary.update(seed_group_stage_results_and_predictions(session, users))
        summary.update(seed_initial_predictions(session, users))
        summary.update(repair_knockout_bracket(session))
        recalculation = recalculate_competition_state(session)
        session.commit()
        return {
            "users": [
                {"email": users[0].email, "name": users[0].full_name},
                {"email": users[1].email, "name": users[1].full_name},
            ],
            "seeded": summary,
            "recalculation": {
                "standings": recalculation.standings.updated_count,
                "bracket": recalculation.bracket.updated_count,
                "match_points": recalculation.match_points.updated_count,
                "competition_points": recalculation.competition_points.updated_count,
                "ranking": [
                    {
                        "rank": row.rank,
                        "user": row.full_name,
                        "total_points": row.total_points,
                        "match_points": row.match_points,
                        "bonus_points": row.bonus_points,
                    }
                    for row in recalculation.ranking_rows
                ],
            },
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    print(json.dumps(run(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
