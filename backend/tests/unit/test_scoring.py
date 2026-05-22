from __future__ import annotations

import pytest

from app.domain.scoring import (
    MatchScoreInput,
    OfficialMatchResult,
    ScoreRules,
    score_champion_prediction,
    score_match_prediction,
    score_top_scorer_prediction,
)


@pytest.fixture
def score_rules() -> ScoreRules:
    return ScoreRules(
        exact_points=3,
        result_points=1,
        brazil_multiplier=2,
        champion_points=10,
        top_scorer_points=15,
    )


def test_score_match_prediction_exact_result(score_rules: ScoreRules) -> None:
    prediction = MatchScoreInput(home_goals=2, away_goals=1)
    official = OfficialMatchResult(home_goals=2, away_goals=1)
    assert score_match_prediction(prediction, official, score_rules) == 3


def test_score_match_prediction_correct_outcome_only(score_rules: ScoreRules) -> None:
    prediction = MatchScoreInput(home_goals=3, away_goals=2)
    official = OfficialMatchResult(home_goals=1, away_goals=0)
    assert score_match_prediction(prediction, official, score_rules) == 1


def test_score_match_prediction_brazil_multiplier(score_rules: ScoreRules) -> None:
    prediction = MatchScoreInput(home_goals=1, away_goals=1)
    official = OfficialMatchResult(home_goals=1, away_goals=1, involves_brazil=True)
    assert score_match_prediction(prediction, official, score_rules) == 6


def test_score_champion_prediction(score_rules: ScoreRules) -> None:
    assert score_champion_prediction("BRA", "BRA", score_rules) == 10
    assert score_champion_prediction("BRA", "ARG", score_rules) == 0


def test_score_top_scorer_prediction(score_rules: ScoreRules) -> None:
    assert score_top_scorer_prediction("player-1", {"player-1", "player-2"}, score_rules) == 15
    assert score_top_scorer_prediction("player-3", {"player-1", "player-2"}, score_rules) == 0
