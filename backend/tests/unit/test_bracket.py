from __future__ import annotations

from app.domain.bracket import (
    KnockoutMatch,
    QualifiedThirdPlaceTeam,
    allocate_third_place_slots,
    propagate_knockout_results,
)


def test_allocate_third_place_slots_uses_static_matrix() -> None:
    teams = (
        QualifiedThirdPlaceTeam("A", "TEAM_A"),
        QualifiedThirdPlaceTeam("B", "TEAM_B"),
        QualifiedThirdPlaceTeam("C", "TEAM_C"),
        QualifiedThirdPlaceTeam("D", "TEAM_D"),
        QualifiedThirdPlaceTeam("E", "TEAM_E"),
        QualifiedThirdPlaceTeam("F", "TEAM_F"),
        QualifiedThirdPlaceTeam("G", "TEAM_G"),
        QualifiedThirdPlaceTeam("H", "TEAM_H"),
    )
    allocations = allocate_third_place_slots(teams)
    assert len(allocations) == 8
    assert {item.slot for item in allocations} == {"M74", "M77", "M79", "M80", "M81", "M82", "M85", "M87"}


def test_propagate_knockout_results_advances_winners_and_semifinal_losers() -> None:
    matches = (
        KnockoutMatch(slot="M101", home_team_key="BRA", away_team_key="ARG", winner_team_key="BRA"),
        KnockoutMatch(slot="M102", home_team_key="FRA", away_team_key="ESP", winner_team_key="ESP"),
        KnockoutMatch(slot="M103", feeder_home_key="L101", feeder_away_key="L102"),
        KnockoutMatch(slot="M104", feeder_home_key="W101", feeder_away_key="W102"),
    )
    propagated = {match.slot: match for match in propagate_knockout_results(matches)}
    assert propagated["M104"].home_team_key == "BRA"
    assert propagated["M104"].away_team_key == "ESP"
    assert propagated["M103"].home_team_key == "ARG"
    assert propagated["M103"].away_team_key == "FRA"
