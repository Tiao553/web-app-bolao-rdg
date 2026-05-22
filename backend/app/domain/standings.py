from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar


@dataclass(frozen=True, slots=True)
class GroupTeamSeed:
    group_name: str
    team_key: str
    fifa_ranking: int | None = None


@dataclass(frozen=True, slots=True)
class GroupMatchResult:
    group_name: str
    home_team_key: str
    away_team_key: str
    home_goals: int
    away_goals: int


@dataclass(frozen=True, slots=True)
class TeamStanding:
    position: int
    group_name: str
    team_key: str
    fifa_ranking: int | None
    matches_played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    away_goals: int
    points: int


@dataclass(frozen=True, slots=True)
class RankedThirdPlaceTeam:
    rank: int
    group_name: str
    team_key: str
    fifa_ranking: int | None
    points: int
    goal_difference: int
    goals_for: int
    advances: bool


@dataclass(slots=True)
class _MutableStanding:
    group_name: str
    team_key: str
    fifa_ranking: int | None
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    away_goals: int = 0
    points: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


_T = TypeVar("_T")


def build_group_standings(
    group_name: str,
    teams: Sequence[GroupTeamSeed],
    matches: Iterable[GroupMatchResult],
) -> tuple[TeamStanding, ...]:
    seeds = _normalize_group_seeds(group_name, teams)
    group_matches = _normalize_group_matches(group_name, seeds, matches)
    aggregate = _build_aggregate_stats(seeds, group_matches)
    ordered_team_keys = _rank_group_team_keys(tuple(aggregate), aggregate, group_matches)
    standings: list[TeamStanding] = []
    for index, team_key in enumerate(ordered_team_keys, start=1):
        stats = aggregate[team_key]
        standings.append(
            TeamStanding(
                position=index,
                group_name=stats.group_name,
                team_key=stats.team_key,
                fifa_ranking=stats.fifa_ranking,
                matches_played=stats.matches_played,
                wins=stats.wins,
                draws=stats.draws,
                losses=stats.losses,
                goals_for=stats.goals_for,
                goals_against=stats.goals_against,
                goal_difference=stats.goal_difference,
                away_goals=stats.away_goals,
                points=stats.points,
            )
        )
    return tuple(standings)


def build_all_group_standings(
    teams: Iterable[GroupTeamSeed],
    matches: Iterable[GroupMatchResult],
) -> dict[str, tuple[TeamStanding, ...]]:
    grouped_teams: dict[str, list[GroupTeamSeed]] = defaultdict(list)
    grouped_matches: dict[str, list[GroupMatchResult]] = defaultdict(list)
    for team in teams:
        grouped_teams[team.group_name].append(team)
    for match in matches:
        grouped_matches[match.group_name].append(match)
    standings_by_group: dict[str, tuple[TeamStanding, ...]] = {}
    for group_name in sorted(grouped_teams):
        standings_by_group[group_name] = build_group_standings(
            group_name,
            grouped_teams[group_name],
            grouped_matches.get(group_name, ()),
        )
    return standings_by_group


def extract_third_place_standings(
    standings_by_group: Mapping[str, Sequence[TeamStanding]],
) -> tuple[TeamStanding, ...]:
    return tuple(standings_by_group[group_name][2] for group_name in sorted(standings_by_group))


def rank_third_placed_teams(
    third_place_rows: Iterable[TeamStanding],
) -> tuple[RankedThirdPlaceTeam, ...]:
    rows = tuple(third_place_rows)
    by_team = {row.team_key: row for row in rows}
    ordered = _rank_with_partition_criteria(
        [row.team_key for row in rows],
        criteria=(
            lambda team_key: by_team[team_key].points,
            lambda team_key: by_team[team_key].goal_difference,
            lambda team_key: by_team[team_key].goals_for,
        ),
        final_key=lambda team_key: (
            _ranking_sort_value(by_team[team_key].fifa_ranking),
            by_team[team_key].group_name,
            team_key,
        ),
    )
    ranked_rows: list[RankedThirdPlaceTeam] = []
    for index, team_key in enumerate(ordered, start=1):
        row = by_team[team_key]
        ranked_rows.append(
            RankedThirdPlaceTeam(
                rank=index,
                group_name=row.group_name,
                team_key=row.team_key,
                fifa_ranking=row.fifa_ranking,
                points=row.points,
                goal_difference=row.goal_difference,
                goals_for=row.goals_for,
                advances=index <= 8,
            )
        )
    return tuple(ranked_rows)


def select_best_third_placed_teams(
    third_place_rows: Iterable[TeamStanding],
) -> tuple[RankedThirdPlaceTeam, ...]:
    return tuple(row for row in rank_third_placed_teams(third_place_rows) if row.advances)


def _normalize_group_seeds(
    group_name: str,
    teams: Sequence[GroupTeamSeed],
) -> dict[str, GroupTeamSeed]:
    seeds: dict[str, GroupTeamSeed] = {}
    for team in teams:
        if team.group_name != group_name:
            raise ValueError(f"team {team.team_key} does not belong to group {group_name}")
        seeds[team.team_key] = team
    if not seeds:
        raise ValueError(f"group {group_name} must contain at least one team")
    return seeds


def _normalize_group_matches(
    group_name: str,
    seeds: Mapping[str, GroupTeamSeed],
    matches: Iterable[GroupMatchResult],
) -> tuple[GroupMatchResult, ...]:
    normalized: list[GroupMatchResult] = []
    for match in matches:
        if match.group_name != group_name:
            raise ValueError(f"match does not belong to group {group_name}")
        if match.home_team_key not in seeds or match.away_team_key not in seeds:
            raise ValueError(f"match contains a team outside of group {group_name}")
        normalized.append(match)
    return tuple(normalized)


def _build_aggregate_stats(
    seeds: Mapping[str, GroupTeamSeed],
    matches: Iterable[GroupMatchResult],
) -> dict[str, _MutableStanding]:
    stats = {
        team_key: _MutableStanding(
            group_name=seed.group_name,
            team_key=seed.team_key,
            fifa_ranking=seed.fifa_ranking,
        )
        for team_key, seed in seeds.items()
    }
    for match in matches:
        _apply_match(stats[match.home_team_key], stats[match.away_team_key], match)
    return stats


def _apply_match(
    home: _MutableStanding,
    away: _MutableStanding,
    match: GroupMatchResult,
) -> None:
    home.matches_played += 1
    away.matches_played += 1
    home.goals_for += match.home_goals
    home.goals_against += match.away_goals
    away.goals_for += match.away_goals
    away.goals_against += match.home_goals
    away.away_goals += match.away_goals
    if match.home_goals > match.away_goals:
        home.wins += 1
        away.losses += 1
        home.points += 3
        return
    if match.home_goals < match.away_goals:
        away.wins += 1
        home.losses += 1
        away.points += 3
        return
    home.draws += 1
    away.draws += 1
    home.points += 1
    away.points += 1


def _rank_group_team_keys(
    team_keys: tuple[str, ...],
    aggregate: Mapping[str, _MutableStanding],
    matches: tuple[GroupMatchResult, ...],
) -> list[str]:
    ranked_by_full = sorted(
        team_keys,
        key=lambda team_key: (
            aggregate[team_key].points,
            aggregate[team_key].goal_difference,
            aggregate[team_key].goals_for,
        ),
        reverse=True,
    )
    ordered: list[str] = []
    for bucket in _group_equal_items(
        ranked_by_full,
        key=lambda team_key: (
            aggregate[team_key].points,
            aggregate[team_key].goal_difference,
            aggregate[team_key].goals_for,
        ),
    ):
        if len(bucket) == 1:
            ordered.extend(bucket)
            continue
        head_to_head = _build_head_to_head_stats(bucket, aggregate, matches)

        def head_to_head_points(
            team_key: str,
            table: Mapping[str, _MutableStanding] = head_to_head,
        ) -> int:
            return table[team_key].points

        def head_to_head_goal_difference(
            team_key: str,
            table: Mapping[str, _MutableStanding] = head_to_head,
        ) -> int:
            return table[team_key].goal_difference

        def head_to_head_goals_for(
            team_key: str,
            table: Mapping[str, _MutableStanding] = head_to_head,
        ) -> int:
            return table[team_key].goals_for

        def head_to_head_away_goals(
            team_key: str,
            table: Mapping[str, _MutableStanding] = head_to_head,
        ) -> int:
            return table[team_key].away_goals

        ordered.extend(
            _rank_with_partition_criteria(
                bucket,
                criteria=(
                    head_to_head_points,
                    head_to_head_goal_difference,
                    head_to_head_goals_for,
                    head_to_head_away_goals,
                ),
                final_key=lambda team_key: (
                    _ranking_sort_value(aggregate[team_key].fifa_ranking),
                    team_key,
                ),
            )
        )
    return ordered


def _build_head_to_head_stats(
    team_keys: Sequence[str],
    aggregate: Mapping[str, _MutableStanding],
    matches: Iterable[GroupMatchResult],
) -> dict[str, _MutableStanding]:
    subset = set(team_keys)
    head_to_head = {
        team_key: _MutableStanding(
            group_name=aggregate[team_key].group_name,
            team_key=team_key,
            fifa_ranking=aggregate[team_key].fifa_ranking,
        )
        for team_key in team_keys
    }
    for match in matches:
        if match.home_team_key in subset and match.away_team_key in subset:
            _apply_match(
                head_to_head[match.home_team_key],
                head_to_head[match.away_team_key],
                match,
            )
    return head_to_head


def _rank_with_partition_criteria(
    team_keys: Sequence[str],
    criteria: Sequence[Callable[[str], int]],
    final_key: Callable[[str], tuple[int | str, ...]],
) -> list[str]:
    return _rank_partition(list(team_keys), criteria, final_key, 0)


def _rank_partition(
    team_keys: list[str],
    criteria: Sequence[Callable[[str], int]],
    final_key: Callable[[str], tuple[int | str, ...]],
    depth: int,
) -> list[str]:
    if len(team_keys) <= 1:
        return list(team_keys)
    if depth >= len(criteria):
        return sorted(team_keys, key=final_key)
    key_fn = criteria[depth]
    sorted_keys = sorted(team_keys, key=key_fn, reverse=True)
    ordered: list[str] = []
    for bucket in _group_equal_items(sorted_keys, key=key_fn):
        if len(bucket) == 1:
            ordered.extend(bucket)
            continue
        ordered.extend(_rank_partition(bucket, criteria, final_key, depth + 1))
    return ordered


def _group_equal_items(items: Sequence[_T], key: Callable[[_T], object]) -> list[list[_T]]:
    grouped: list[list[_T]] = []
    current_bucket: list[_T] = []
    sentinel = object()
    current_key: object = sentinel
    for item in items:
        item_key = key(item)
        if current_key is sentinel or item_key == current_key:
            current_bucket.append(item)
            current_key = item_key
            continue
        grouped.append(current_bucket)
        current_bucket = [item]
        current_key = item_key
    if current_bucket:
        grouped.append(current_bucket)
    return grouped


def _ranking_sort_value(value: int | None) -> int:
    return value if value is not None else 10**9
