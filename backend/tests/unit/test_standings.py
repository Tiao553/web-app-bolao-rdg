from __future__ import annotations

from app.domain.standings import (
    GroupMatchResult,
    GroupTeamSeed,
    build_group_standings,
    rank_third_placed_teams,
)


def test_build_group_standings_uses_points_goal_difference_and_goals_for() -> None:
    teams = (
        GroupTeamSeed(group_name="A", team_key="BRA", fifa_ranking=1),
        GroupTeamSeed(group_name="A", team_key="ARG", fifa_ranking=2),
        GroupTeamSeed(group_name="A", team_key="USA", fifa_ranking=3),
        GroupTeamSeed(group_name="A", team_key="JPN", fifa_ranking=4),
    )
    matches = (
        GroupMatchResult("A", "BRA", "ARG", 2, 0),
        GroupMatchResult("A", "USA", "JPN", 1, 1),
        GroupMatchResult("A", "BRA", "USA", 1, 0),
        GroupMatchResult("A", "ARG", "JPN", 3, 1),
        GroupMatchResult("A", "BRA", "JPN", 1, 1),
        GroupMatchResult("A", "ARG", "USA", 0, 0),
    )
    standings = build_group_standings("A", teams, matches)
    assert [row.team_key for row in standings] == ["BRA", "ARG", "USA", "JPN"]
    assert standings[0].points == 7
    assert standings[2].position == 3


def test_build_group_standings_head_to_head_breaks_tie() -> None:
    teams = (
        GroupTeamSeed(group_name="B", team_key="MEX", fifa_ranking=10),
        GroupTeamSeed(group_name="B", team_key="GER", fifa_ranking=20),
        GroupTeamSeed(group_name="B", team_key="NED", fifa_ranking=30),
        GroupTeamSeed(group_name="B", team_key="EGY", fifa_ranking=40),
    )
    matches = (
        GroupMatchResult("B", "MEX", "GER", 1, 0),
        GroupMatchResult("B", "NED", "EGY", 1, 0),
        GroupMatchResult("B", "MEX", "NED", 0, 1),
        GroupMatchResult("B", "GER", "EGY", 2, 1),
        GroupMatchResult("B", "MEX", "EGY", 2, 0),
        GroupMatchResult("B", "GER", "NED", 1, 0),
    )
    standings = build_group_standings("B", teams, matches)
    assert [row.team_key for row in standings[:3]] == ["MEX", "GER", "NED"]


def test_rank_third_placed_teams_marks_best_eight() -> None:
    rows = [
        build_group_standings(
            group_name,
            (
                GroupTeamSeed(group_name, f"{group_name}1", 1),
                GroupTeamSeed(group_name, f"{group_name}2", 2),
                GroupTeamSeed(group_name, f"{group_name}3", 3),
                GroupTeamSeed(group_name, f"{group_name}4", 4),
            ),
            (
                GroupMatchResult(group_name, f"{group_name}1", f"{group_name}2", 1, 0),
                GroupMatchResult(group_name, f"{group_name}3", f"{group_name}4", 1, 0),
                GroupMatchResult(group_name, f"{group_name}1", f"{group_name}3", 1, 0),
                GroupMatchResult(group_name, f"{group_name}2", f"{group_name}4", 1, 0),
                GroupMatchResult(group_name, f"{group_name}1", f"{group_name}4", 1, 0),
                GroupMatchResult(group_name, f"{group_name}2", f"{group_name}3", 0, 1),
            ),
        )[2]
        for group_name in "ABCDEFGHIJKL"
    ]
    ranked = rank_third_placed_teams(rows)
    assert len(ranked) == 12
    assert sum(1 for row in ranked if row.advances) == 8
    assert ranked[0].rank == 1
