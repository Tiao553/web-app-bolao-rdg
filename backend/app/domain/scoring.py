from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from app.core.config import ScoringSettings, load_yaml_settings


class MatchOutcome(str, Enum):
    HOME_WIN = "HOME_WIN"
    DRAW = "DRAW"
    AWAY_WIN = "AWAY_WIN"


@dataclass(frozen=True, slots=True)
class ScoreRules:
    exact_points: int
    result_points: int
    brazil_multiplier: int
    champion_points: int
    top_scorer_points: int

    def __post_init__(self) -> None:
        numeric_values = (
            self.exact_points,
            self.result_points,
            self.brazil_multiplier,
            self.champion_points,
            self.top_scorer_points,
        )
        if any(value < 0 for value in numeric_values):
            msg = "score rules cannot contain negative values"
            raise ValueError(msg)
        if self.brazil_multiplier < 1:
            msg = "brazil_multiplier must be greater than or equal to 1"
            raise ValueError(msg)

    @classmethod
    def from_settings(cls, settings: ScoringSettings) -> ScoreRules:
        return cls(
            exact_points=settings.exact_points,
            result_points=settings.result_points,
            brazil_multiplier=settings.brazil_multiplier,
            champion_points=settings.champion_points,
            top_scorer_points=settings.top_scorer_points,
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, int]) -> ScoreRules:
        return cls(
            exact_points=payload["exact_points"],
            result_points=payload["result_points"],
            brazil_multiplier=payload["brazil_multiplier"],
            champion_points=payload["champion_points"],
            top_scorer_points=payload["top_scorer_points"],
        )

    @classmethod
    def load(cls, config_path: Path | None = None) -> ScoreRules:
        file_settings = load_yaml_settings(config_path)
        return cls.from_settings(file_settings.scoring)


@dataclass(frozen=True, slots=True)
class MatchScoreInput:
    home_goals: int
    away_goals: int

    def __post_init__(self) -> None:
        if self.home_goals < 0 or self.away_goals < 0:
            msg = "goal predictions must be greater than or equal to zero"
            raise ValueError(msg)

    @property
    def outcome(self) -> MatchOutcome:
        return resolve_match_outcome(self.home_goals, self.away_goals)


@dataclass(frozen=True, slots=True)
class OfficialMatchResult:
    home_goals: int
    away_goals: int
    involves_brazil: bool = False

    def __post_init__(self) -> None:
        if self.home_goals < 0 or self.away_goals < 0:
            msg = "official goals must be greater than or equal to zero"
            raise ValueError(msg)

    @property
    def outcome(self) -> MatchOutcome:
        return resolve_match_outcome(self.home_goals, self.away_goals)


def load_score_rules(config_path: Path | None = None) -> ScoreRules:
    return ScoreRules.load(config_path)


def resolve_match_outcome(home_goals: int, away_goals: int) -> MatchOutcome:
    if home_goals > away_goals:
        return MatchOutcome.HOME_WIN
    if home_goals < away_goals:
        return MatchOutcome.AWAY_WIN
    return MatchOutcome.DRAW


def is_exact_match_prediction(
    prediction: MatchScoreInput,
    official_result: OfficialMatchResult,
) -> bool:
    return (
        prediction.home_goals == official_result.home_goals
        and prediction.away_goals == official_result.away_goals
    )


def is_correct_match_outcome(
    prediction: MatchScoreInput,
    official_result: OfficialMatchResult,
) -> bool:
    return prediction.outcome == official_result.outcome


def score_match_prediction(
    prediction: MatchScoreInput,
    official_result: OfficialMatchResult,
    rules: ScoreRules,
) -> int:
    if is_exact_match_prediction(prediction, official_result):
        base_score = rules.exact_points
    elif is_correct_match_outcome(prediction, official_result):
        base_score = rules.result_points
    else:
        base_score = 0
    if base_score == 0:
        return 0
    if official_result.involves_brazil:
        return base_score * rules.brazil_multiplier
    return base_score


def score_champion_prediction(
    prediction_key: str | None,
    official_champion_key: str | None,
    rules: ScoreRules,
) -> int:
    if prediction_key is None or official_champion_key is None:
        return 0
    if prediction_key != official_champion_key:
        return 0
    return rules.champion_points


def score_top_scorer_prediction(
    prediction_key: str | None,
    official_top_scorer_keys: Iterable[str],
    rules: ScoreRules,
) -> int:
    if prediction_key is None:
        return 0
    winners = {key for key in official_top_scorer_keys}
    if prediction_key not in winners:
        return 0
    return rules.top_scorer_points
