from __future__ import annotations

from app.domain.bracket import (
    KnockoutMatch,
    QualifiedThirdPlaceTeam,
    allocate_third_place_slots,
    propagate_knockout_results,
)
from app.models.schema import CompetitionPhase, Match
from app.services.recalculation_service import _resolve_winner_team_key


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


def test_resolve_winner_team_key_prefers_terminal_scores() -> None:
    home_winner = Match(
        phase=CompetitionPhase.ROUND_OF_32,
        bracket_slot="M73",
        home_team_name="Brasil",
        away_team_name="Canadá",
        home_team_fifa_code="BRA",
        away_team_fifa_code="CAN",
        status="FT",
        official_home_goals=2,
        official_away_goals=1,
        winner_team_name="Canadá",
    )
    away_winner = Match(
        phase=CompetitionPhase.ROUND_OF_32,
        bracket_slot="M74",
        home_team_name="Alemanha",
        away_team_name="Bosnia and Herzegovina",
        home_team_fifa_code="GER",
        away_team_fifa_code="BIH",
        status="FT",
        official_home_goals=0,
        official_away_goals=1,
    )

    assert _resolve_winner_team_key(home_winner) == "BRA"
    assert _resolve_winner_team_key(away_winner) == "BIH"


def test_resolve_winner_team_key_handles_tied_penalty_winner_name_safely() -> None:
    resolved = Match(
        phase=CompetitionPhase.ROUND_OF_32,
        bracket_slot="M73",
        home_team_name="Brasil",
        away_team_name="Canadá",
        home_team_fifa_code="BRA",
        away_team_fifa_code="CAN",
        status="PEN",
        official_home_goals=1,
        official_away_goals=1,
        winner_team_name="Brazil",
    )
    unresolved = Match(
        phase=CompetitionPhase.ROUND_OF_32,
        bracket_slot="M74",
        home_team_name="Alemanha",
        away_team_name="Bosnia and Herzegovina",
        home_team_fifa_code="GER",
        away_team_fifa_code="BIH",
        status="PEN",
        official_home_goals=1,
        official_away_goals=1,
        winner_team_name="Somebody else",
    )

    assert _resolve_winner_team_key(resolved) == "BRA"
    assert _resolve_winner_team_key(unresolved) is None


def test_propagate_knockout_results_uses_real_world_cup_slot_chain() -> None:
    matches = (
        KnockoutMatch(slot="M73", home_team_key="RSA", away_team_key="CAN", winner_team_key="CAN"),
        KnockoutMatch(slot="M74", home_team_key="GER", away_team_key="PAR", winner_team_key="PAR"),
        KnockoutMatch(slot="M75", home_team_key="NED", away_team_key="MAR", winner_team_key="MAR"),
        KnockoutMatch(slot="M76", home_team_key="BRA", away_team_key="JPN", winner_team_key="BRA"),
        KnockoutMatch(slot="M77", home_team_key="FRA", away_team_key="SWE", winner_team_key="FRA"),
        KnockoutMatch(slot="M78", home_team_key="CIV", away_team_key="NOR", winner_team_key="NOR"),
        KnockoutMatch(slot="M79", home_team_key="MEX", away_team_key="ECU", winner_team_key="MEX"),
        KnockoutMatch(slot="M80", home_team_key="ENG", away_team_key="COD", winner_team_key="ENG"),
        KnockoutMatch(slot="M89", feeder_home_key="W74", feeder_away_key="W77", winner_team_key="FRA"),
        KnockoutMatch(slot="M90", feeder_home_key="W73", feeder_away_key="W75", winner_team_key="CAN"),
        KnockoutMatch(slot="M91", feeder_home_key="W76", feeder_away_key="W78", winner_team_key="BRA"),
        KnockoutMatch(slot="M92", feeder_home_key="W79", feeder_away_key="W80", winner_team_key="MEX"),
        KnockoutMatch(slot="M97", feeder_home_key="W89", feeder_away_key="W90", winner_team_key="FRA"),
        KnockoutMatch(slot="M99", feeder_home_key="W91", feeder_away_key="W92", winner_team_key="BRA"),
        KnockoutMatch(slot="M101", feeder_home_key="W97", feeder_away_key="W98", winner_team_key="FRA"),
        KnockoutMatch(slot="M102", feeder_home_key="W99", feeder_away_key="W100", winner_team_key="BRA"),
        KnockoutMatch(slot="M104", feeder_home_key="W101", feeder_away_key="W102"),
    )

    propagated = {match.slot: match for match in propagate_knockout_results(matches)}

    assert propagated["M89"].home_team_key == "PAR"
    assert propagated["M89"].away_team_key == "FRA"
    assert propagated["M90"].home_team_key == "CAN"
    assert propagated["M90"].away_team_key == "MAR"
    assert propagated["M91"].home_team_key == "BRA"
    assert propagated["M91"].away_team_key == "NOR"
    assert propagated["M92"].home_team_key == "MEX"
    assert propagated["M92"].away_team_key == "ENG"
    assert propagated["M97"].home_team_key == "FRA"
    assert propagated["M97"].away_team_key == "CAN"
    assert propagated["M99"].home_team_key == "BRA"
    assert propagated["M99"].away_team_key == "MEX"
    assert propagated["M101"].home_team_key == "FRA"
    assert propagated["M104"].home_team_key == "FRA"
    assert propagated["M104"].away_team_key == "BRA"
