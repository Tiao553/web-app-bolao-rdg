from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path

THIRD_PLACE_SLOT_ORDER: tuple[str, ...] = (
    "M74",
    "M77",
    "M79",
    "M80",
    "M81",
    "M82",
    "M85",
    "M87",
)


@dataclass(frozen=True, slots=True)
class QualifiedThirdPlaceTeam:
    group_name: str
    team_key: str
    fifa_ranking: int | None = None


@dataclass(frozen=True, slots=True)
class ThirdPlaceSlotAssignment:
    slot: str
    group_name: str
    team_key: str


@dataclass(frozen=True, slots=True)
class KnockoutMatch:
    slot: str
    home_team_key: str | None = None
    away_team_key: str | None = None
    feeder_home_key: str | None = None
    feeder_away_key: str | None = None
    winner_team_key: str | None = None
    loser_team_key: str | None = None


def get_default_matrix_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "third_place_slot_matrix.json"


def load_third_place_slot_matrix(matrix_path: Path | None = None) -> dict[str, dict[str, str]]:
    resolved_path = matrix_path or get_default_matrix_path()
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, dict):
        raise ValueError(f"invalid third-place slot matrix in {resolved_path}")
    return {str(key): dict(value) for key, value in scenarios.items()}


def normalize_combination_key(group_names: Iterable[str]) -> str:
    normalized_groups = sorted({group_name.strip() for group_name in group_names})
    if len(normalized_groups) != 8:
        raise ValueError("third-place allocation requires exactly eight unique group names")
    return "".join(normalized_groups)


def allocate_third_place_slots(
    qualified_teams: Iterable[QualifiedThirdPlaceTeam],
    matrix: dict[str, dict[str, str]] | None = None,
) -> tuple[ThirdPlaceSlotAssignment, ...]:
    qualified_list = tuple(qualified_teams)
    teams_by_group = {team.group_name: team for team in qualified_list}
    combination_key = normalize_combination_key(teams_by_group)
    resolved_matrix = matrix or load_third_place_slot_matrix()
    scenario = resolved_matrix.get(combination_key)
    if scenario is None:
        raise ValueError(f"no third-place allocation scenario for {combination_key}")
    return tuple(
        ThirdPlaceSlotAssignment(
            slot=slot,
            group_name=scenario[slot],
            team_key=teams_by_group[scenario[slot]].team_key,
        )
        for slot in THIRD_PLACE_SLOT_ORDER
    )


def apply_third_place_allocations(
    matches: Iterable[KnockoutMatch],
    allocations: Iterable[ThirdPlaceSlotAssignment],
) -> tuple[KnockoutMatch, ...]:
    by_slot = {match.slot: match for match in matches}
    for allocation in allocations:
        by_slot[allocation.slot] = replace(
            by_slot[allocation.slot],
            away_team_key=allocation.team_key,
        )
    return _sort_matches(by_slot.values())


def propagate_knockout_results(matches: Iterable[KnockoutMatch]) -> tuple[KnockoutMatch, ...]:
    by_slot = {match.slot: match for match in matches}
    for source_match in _sort_matches(by_slot.values()):
        winner_key = source_match.winner_team_key
        loser_key = resolve_loser_team(source_match)
        suffix = source_match.slot.removeprefix("M")
        winner_feeder = f"W{suffix}"
        loser_feeder = f"L{suffix}"
        for target_slot, target_match in tuple(by_slot.items()):
            updated_match = target_match
            if winner_key is not None and target_match.feeder_home_key == winner_feeder:
                updated_match = replace(updated_match, home_team_key=winner_key)
            if winner_key is not None and target_match.feeder_away_key == winner_feeder:
                updated_match = replace(updated_match, away_team_key=winner_key)
            if loser_key is not None and target_match.feeder_home_key == loser_feeder:
                updated_match = replace(updated_match, home_team_key=loser_key)
            if loser_key is not None and target_match.feeder_away_key == loser_feeder:
                updated_match = replace(updated_match, away_team_key=loser_key)
            by_slot[target_slot] = updated_match
    return _sort_matches(by_slot.values())


def resolve_loser_team(match: KnockoutMatch) -> str | None:
    if match.loser_team_key is not None:
        return match.loser_team_key
    if match.winner_team_key is None:
        return None
    if match.home_team_key is None or match.away_team_key is None:
        return None
    if match.winner_team_key == match.home_team_key:
        return match.away_team_key
    if match.winner_team_key == match.away_team_key:
        return match.home_team_key
    raise ValueError(f"winner {match.winner_team_key} is not part of match {match.slot}")


def _sort_matches(matches: Iterable[KnockoutMatch]) -> tuple[KnockoutMatch, ...]:
    return tuple(sorted(matches, key=lambda match: int(match.slot.removeprefix("M"))))
