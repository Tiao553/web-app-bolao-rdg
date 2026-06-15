from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.schemas.frontend import MemberBracketScreenDto, MemberResultsScreenDto
from app.core.security import build_auth_error, require_approved_user
from app.models.schema import (
    CompetitionPhase,
    CompetitionPhaseConfig,
    CompetitionPrediction,
    CompetitionWindow,
    AccessStatus,
    Match,
    MatchPrediction,
    PredictionType,
    User,
)
from app.repositories.queries import (
    CompetitionWindowSnapshot,
    get_active_scoring_rule,
    get_competition_prediction,
    get_competition_window_dependency,
    get_db_session,
    get_match_by_id,
    get_match_prediction,
    ranking_users_select,
    list_active_competition_phase_configs,
)
from app.services.frontend_contract_service import FrontendContractService
from app.services.match_status import is_terminal_match_status
from app.services.team_metadata import (
    get_players_by_id,
    get_team_metadata,
    iso2_to_flag,
)

import os as _os
_DATA_DIR = Path(_os.environ.get("DATA_DIR", str(Path(__file__).parent.parent.parent.parent / "data")))


@lru_cache(maxsize=1)
def _load_teams() -> list[dict]:
    path = _DATA_DIR / "teams-groups.json"
    if not path.exists():
        return []
    with path.open() as f:
        teams = json.load(f).get("teams", [])
    return [
        {**team, "flag": iso2_to_flag(team.get("iso2") if isinstance(team, dict) else None)}
        for team in teams
        if isinstance(team, dict)
    ]


@lru_cache(maxsize=1)
def _load_players() -> list[dict]:
    path = _DATA_DIR / "players-attackers.json"
    if not path.exists():
        return []
    with path.open() as f:
        return json.load(f).get("players", [])

router = APIRouter(prefix="/api/member", tags=["member"])


@dataclass(frozen=True, slots=True)
class RankingRowData:
    rank: int
    user_id: UUID
    full_name: str
    total_points: int
    match_points: int
    exact_points: int
    result_points: int
    brazil_points: int
    bonus_points: int


class RankingBreakdownResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matchPoints: int
    exactPoints: int
    resultPoints: int
    brazilPoints: int
    championPoints: int
    topScorerPoints: int
    bonusPoints: int
    totalPoints: int


class CompetitionWindowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predictionCloseAt: datetime
    exploreReleaseAt: datetime
    predictionLocked: bool
    exploreReleased: bool


class DashboardUserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    email: str
    name: str
    accessStatus: str
    isAdmin: bool


class NextMatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    homeTeam: str
    homeCode: str | None
    homeIso2: str | None
    homeFlag: str
    awayTeam: str
    awayCode: str | None
    awayIso2: str | None
    awayFlag: str
    startsAt: str
    involvesBrazil: bool


class DashboardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: DashboardUserResponse
    competition: CompetitionWindowResponse
    nextLockAt: datetime | None
    rankingPosition: int | None
    totalPoints: int
    savedMatchPredictions: int
    savedBonusPredictions: int
    nextMatches: list[NextMatchResponse]


class MatchPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    home_goals: int = Field(ge=0, le=50)
    away_goals: int = Field(ge=0, le=50)


class CompetitionPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selection_key: str = Field(min_length=1, max_length=128)
    selection_label: str = Field(min_length=1, max_length=255)


class MatchPredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    matchId: UUID
    homeGoals: int
    awayGoals: int
    pointsAwarded: int | None
    lockedAt: datetime | None


class CompetitionPredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    predictionType: PredictionType
    selectionKey: str
    selectionLabel: str
    pointsAwarded: int | None
    lockedAt: datetime | None


class MemberPredictionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    competition: CompetitionWindowResponse
    matchPredictions: list[MatchPredictionResponse]
    competitionPredictions: list[CompetitionPredictionResponse]


class RankingRowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int
    userId: UUID
    fullName: str
    totalPoints: int
    matchPoints: int
    exactPoints: int
    resultPoints: int
    brazilPoints: int
    bonusPoints: int


class RankingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[RankingRowResponse]
    currentUserRank: int | None
    currentUserBreakdown: RankingBreakdownResponse | None


class ExploreMatchPredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    userId: UUID
    userName: str
    matchId: UUID
    phase: str
    stageRound: int | None
    groupName: str | None
    startsAt: datetime | None
    status: str
    homeTeam: str
    homeCode: str | None
    homeIso2: str | None
    homeFlag: str
    awayTeam: str
    awayCode: str | None
    awayIso2: str | None
    awayFlag: str
    homeGoals: int
    awayGoals: int
    pointsAwarded: int | None


class ExploreMatchGroupResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matchId: UUID
    phase: str
    stageRound: int | None
    groupName: str | None
    startsAt: datetime | None
    status: str
    homeTeam: str
    homeCode: str | None
    homeIso2: str | None
    homeFlag: str
    awayTeam: str
    awayCode: str | None
    awayIso2: str | None
    awayFlag: str
    predictions: list[ExploreMatchPredictionResponse]


class ExploreCompetitionPredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    userId: UUID
    userName: str
    predictionType: PredictionType
    selectionKey: str
    selectionLabel: str
    selectionTeamCode: str | None
    selectionTeamName: str | None
    selectionTeamIso2: str | None
    selectionTeamFlag: str | None
    pointsAwarded: int | None


class ExploreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exploreState: Literal["locked", "partial", "released"]
    exploreReleased: bool
    matchGroups: list[ExploreMatchGroupResponse]
    matchPredictions: list[ExploreMatchPredictionResponse]
    competitionPredictions: list[ExploreCompetitionPredictionResponse]


def build_explore_match_prediction_response(
    prediction: MatchPrediction,
) -> ExploreMatchPredictionResponse:
    match = prediction.match
    home_team = get_team_metadata(match.home_team_fifa_code, match.home_team_name)
    away_team = get_team_metadata(match.away_team_fifa_code, match.away_team_name)

    return ExploreMatchPredictionResponse(
        userId=prediction.user_id,
        userName=prediction.user.full_name,
        matchId=prediction.match_id,
        phase=match.phase.value,
        stageRound=match.stage_round,
        groupName=match.group_name,
        startsAt=match.starts_at,
        status=match.status,
        homeTeam=home_team.name,
        homeCode=home_team.code,
        homeIso2=home_team.iso2,
        homeFlag=home_team.flag,
        awayTeam=away_team.name,
        awayCode=away_team.code,
        awayIso2=away_team.iso2,
        awayFlag=away_team.flag,
        homeGoals=prediction.home_goals,
        awayGoals=prediction.away_goals,
        pointsAwarded=prediction.points_awarded,
    )


def build_explore_competition_prediction_response(
    prediction: CompetitionPrediction,
) -> ExploreCompetitionPredictionResponse:
    if prediction.prediction_type == PredictionType.CHAMPION:
        team = get_team_metadata(prediction.selection_key, prediction.selection_label)
        team_code = team.code
        team_name = team.name
        team_iso2 = team.iso2
        team_flag = team.flag
    else:
        player = get_players_by_id().get(prediction.selection_key)
        player_team_code = player.get("teamCode") if isinstance(player, dict) else None
        if isinstance(player_team_code, str) and player_team_code.strip():
            team = get_team_metadata(player_team_code, None)
            team_code = team.code
            team_name = team.name
            team_iso2 = team.iso2
            team_flag = team.flag
        else:
            team_code = None
            team_name = None
            team_iso2 = None
            team_flag = None

    return ExploreCompetitionPredictionResponse(
        userId=prediction.user_id,
        userName=prediction.user.full_name,
        predictionType=prediction.prediction_type,
        selectionKey=prediction.selection_key,
        selectionLabel=prediction.selection_label,
        selectionTeamCode=team_code,
        selectionTeamName=team_name,
        selectionTeamIso2=team_iso2,
        selectionTeamFlag=team_flag,
        pointsAwarded=prediction.points_awarded,
    )


def _is_explore_match_public(
    match: Match,
    *,
    now: datetime,
    db_session: Session,
    phase_configs: dict[str, CompetitionPhaseConfig] | None = None,
) -> bool:
    if is_terminal_match_status(match.status):
        return True
    round_key = _match_round_key(match)
    if round_key is not None:
        configs = phase_configs if phase_configs is not None else _phase_config_map(db_session)
        config = configs.get(round_key)
        if config is not None:
            return config.is_force_locked or now >= as_utc(config.explore_at)
    if match.starts_at is None:
        return False
    return now >= as_utc(match.starts_at) - PHASE_LOCK_OFFSET


def _build_explore_match_group_response(
    *,
    match: Match,
    predictions: list[MatchPrediction],
) -> ExploreMatchGroupResponse:
    home_team = get_team_metadata(match.home_team_fifa_code, match.home_team_name)
    away_team = get_team_metadata(match.away_team_fifa_code, match.away_team_name)
    return ExploreMatchGroupResponse(
        matchId=match.id,
        phase=match.phase.value,
        stageRound=match.stage_round,
        groupName=match.group_name,
        startsAt=match.starts_at,
        status=match.status,
        homeTeam=home_team.name,
        homeCode=home_team.code,
        homeIso2=home_team.iso2,
        homeFlag=home_team.flag,
        awayTeam=away_team.name,
        awayCode=away_team.code,
        awayIso2=away_team.iso2,
        awayFlag=away_team.flag,
        predictions=[
            build_explore_match_prediction_response(prediction)
            for prediction in predictions
        ],
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def build_competition_window_response(
    competition_window: CompetitionWindowSnapshot,
    *,
    now: datetime,
    db_session: Session,
) -> CompetitionWindowResponse:
    phase_configs = _phase_config_map(db_session)
    if phase_configs:
        initial_phase = phase_configs.get("initial_predictions")
        initial_lock_at = as_utc(initial_phase.lock_at) if initial_phase is not None else as_utc(competition_window.prediction_close_at)
        initial_explore_at = as_utc(initial_phase.explore_at) if initial_phase is not None else as_utc(competition_window.explore_release_at)
        prediction_locked = bool(initial_phase and (initial_phase.is_force_locked or now >= initial_lock_at))
        explore_released = bool(initial_phase and (initial_phase.is_force_locked or now >= initial_explore_at))

        return CompetitionWindowResponse(
            predictionCloseAt=initial_lock_at,
            exploreReleaseAt=initial_explore_at,
            predictionLocked=prediction_locked,
            exploreReleased=explore_released,
        )

    return CompetitionWindowResponse(
        predictionCloseAt=as_utc(competition_window.prediction_close_at),
        exploreReleaseAt=as_utc(competition_window.explore_release_at),
        predictionLocked=now >= as_utc(competition_window.prediction_close_at),
        exploreReleased=now >= as_utc(competition_window.explore_release_at),
    )


@dataclass(frozen=True, slots=True)
class RankingMatchBreakdown:
    match_points: int
    exact_points: int
    result_points: int
    brazil_points: int


@dataclass(frozen=True, slots=True)
class RankingBonusBreakdown:
    champion_points: int
    top_scorer_points: int

    @property
    def bonus_points(self) -> int:
        return self.champion_points + self.top_scorer_points


def _empty_match_breakdown() -> RankingMatchBreakdown:
    return RankingMatchBreakdown(
        match_points=0,
        exact_points=0,
        result_points=0,
        brazil_points=0,
    )


def _empty_bonus_breakdown() -> RankingBonusBreakdown:
    return RankingBonusBreakdown(
        champion_points=0,
        top_scorer_points=0,
    )


def build_match_breakdowns(
    db_session: Session,
    *,
    user_ids: list[UUID],
) -> dict[UUID, RankingMatchBreakdown]:
    scoring_rule = get_active_scoring_rule(db_session)
    if not user_ids:
        return {}

    totals_by_user: dict[UUID, list[int]] = {
        user_id: [0, 0, 0]
        for user_id in user_ids
    }
    prediction_rows = db_session.execute(
        select(
            MatchPrediction.user_id,
            MatchPrediction.home_goals,
            MatchPrediction.away_goals,
            Match.official_home_goals,
            Match.official_away_goals,
            Match.involves_brazil,
        )
        .join(Match, Match.id == MatchPrediction.match_id)
        .where(MatchPrediction.user_id.in_(tuple(user_ids)))
        .order_by(MatchPrediction.user_id.asc(), MatchPrediction.created_at.asc(), MatchPrediction.id.asc())
    ).all()

    for (
        user_id,
        predicted_home_goals,
        predicted_away_goals,
        official_home_goals,
        official_away_goals,
        involves_brazil,
    ) in prediction_rows:
        if official_home_goals is None or official_away_goals is None:
            continue
        is_exact = (
            predicted_home_goals == official_home_goals
            and predicted_away_goals == official_away_goals
        )
        same_outcome = False
        if not is_exact:
            prediction_outcome = "HOME" if predicted_home_goals > predicted_away_goals else "AWAY" if predicted_home_goals < predicted_away_goals else "DRAW"
            official_outcome = "HOME" if official_home_goals > official_away_goals else "AWAY" if official_home_goals < official_away_goals else "DRAW"
            same_outcome = prediction_outcome == official_outcome
        if not (is_exact or same_outcome):
            continue

        base_points = scoring_rule.exact_points if is_exact else scoring_rule.result_points
        totals = totals_by_user[user_id]
        if is_exact:
            totals[0] += base_points
        else:
            totals[1] += base_points
        if involves_brazil and scoring_rule.brazil_multiplier > 1:
            totals[2] += base_points * (scoring_rule.brazil_multiplier - 1)

    return {
        user_id: RankingMatchBreakdown(
            match_points=totals[0] + totals[1] + totals[2],
            exact_points=totals[0],
            result_points=totals[1],
            brazil_points=totals[2],
        )
        for user_id, totals in totals_by_user.items()
    }


def build_match_breakdown(db_session: Session, *, user_id: UUID) -> RankingMatchBreakdown:
    return build_match_breakdowns(db_session, user_ids=[user_id]).get(user_id, _empty_match_breakdown())


def build_bonus_breakdowns(
    db_session: Session,
    *,
    user_ids: list[UUID],
) -> dict[UUID, RankingBonusBreakdown]:
    if not user_ids:
        return {}

    latest_points_by_user: dict[UUID, dict[PredictionType, int]] = {
        user_id: {}
        for user_id in user_ids
    }
    prediction_rows = db_session.execute(
        select(
            CompetitionPrediction.user_id,
            CompetitionPrediction.prediction_type,
            CompetitionPrediction.points_awarded,
        )
        .where(CompetitionPrediction.user_id.in_(tuple(user_ids)))
        .order_by(
            CompetitionPrediction.user_id.asc(),
            CompetitionPrediction.prediction_type.asc(),
            CompetitionPrediction.created_at.asc(),
            CompetitionPrediction.id.asc(),
        )
    ).all()

    for user_id, prediction_type, points_awarded in prediction_rows:
        latest_points_by_user[user_id][prediction_type] = int(points_awarded or 0)

    return {
        user_id: RankingBonusBreakdown(
            champion_points=points_by_type.get(PredictionType.CHAMPION, 0),
            top_scorer_points=points_by_type.get(PredictionType.TOP_SCORER, 0),
        )
        for user_id, points_by_type in latest_points_by_user.items()
    }


def build_ranking_rows(db_session: Session) -> list[RankingRowData]:
    approved_users = list(db_session.scalars(ranking_users_select()).all())
    approved_user_ids = [approved_user.id for approved_user in approved_users]
    bonus_breakdowns_by_user = build_bonus_breakdowns(db_session, user_ids=approved_user_ids)
    match_breakdowns_by_user = build_match_breakdowns(db_session, user_ids=approved_user_ids)

    sorted_users = sorted(
        approved_users,
        key=lambda item: (
            -(match_breakdowns_by_user.get(item.id, _empty_match_breakdown()).match_points + bonus_breakdowns_by_user.get(item.id, _empty_bonus_breakdown()).bonus_points),
            item.created_at,
            str(item.id),
        ),
    )

    rows: list[RankingRowData] = []
    for index, approved_user in enumerate(sorted_users, start=1):
        breakdown = match_breakdowns_by_user.get(approved_user.id, _empty_match_breakdown())
        bonus_points = bonus_breakdowns_by_user.get(approved_user.id, _empty_bonus_breakdown()).bonus_points
        rows.append(
            RankingRowData(
                rank=index,
                user_id=approved_user.id,
                full_name=approved_user.full_name,
                total_points=breakdown.match_points + bonus_points,
                match_points=breakdown.match_points,
                exact_points=breakdown.exact_points,
                result_points=breakdown.result_points,
                brazil_points=breakdown.brazil_points,
                bonus_points=bonus_points,
            )
        )
    return rows


def build_current_user_breakdown(db_session: Session, *, user_id: UUID) -> RankingBreakdownResponse:
    breakdown = build_match_breakdowns(db_session, user_ids=[user_id]).get(user_id, _empty_match_breakdown())
    bonus_breakdown = build_bonus_breakdowns(db_session, user_ids=[user_id]).get(user_id, _empty_bonus_breakdown())
    match_points = breakdown.match_points
    bonus_points = bonus_breakdown.bonus_points
    return RankingBreakdownResponse(
        matchPoints=match_points,
        exactPoints=breakdown.exact_points,
        resultPoints=breakdown.result_points,
        brazilPoints=breakdown.brazil_points,
        championPoints=bonus_breakdown.champion_points,
        topScorerPoints=bonus_breakdown.top_scorer_points,
        bonusPoints=bonus_points,
        totalPoints=match_points + bonus_points,
    )


def get_current_user_rank(rows: list[RankingRowData], *, user_id: UUID) -> int | None:
    for row in rows:
        if row.user_id == user_id:
            return row.rank
    return None


@router.get("/dashboard", response_model=DashboardResponse, status_code=status.HTTP_200_OK)
def get_dashboard(
    user: User = Depends(require_approved_user),
    competition_window: CompetitionWindowSnapshot = Depends(get_competition_window_dependency),
    db_session: Session = Depends(get_db_session),
) -> DashboardResponse:
    now = utc_now()
    ranking_rows = build_ranking_rows(db_session)
    match_prediction_count_statement = select(func.count(MatchPrediction.id)).where(
        MatchPrediction.user_id == user.id,
    )
    competition_prediction_count_statement = select(func.count(CompetitionPrediction.id)).where(
        CompetitionPrediction.user_id == user.id,
    )
    total_points = next((row.total_points for row in ranking_rows if row.user_id == user.id), 0)

    next_matches_stmt = (
        select(Match)
        .where(
            Match.status == "SCHEDULED",
            Match.home_team_name != "TBD",
            Match.away_team_name != "TBD",
        )
        .order_by(Match.starts_at.asc())
        .limit(3)
    )
    next_matches = list(db_session.scalars(next_matches_stmt).all())
    phase_configs = _phase_config_map(db_session)
    next_lock_at = _next_lock_at_from_configs(phase_configs, now) if phase_configs else as_utc(competition_window.prediction_close_at)

    return DashboardResponse(
        user=DashboardUserResponse(
            id=user.id,
            email=user.email,
            name=user.full_name,
            accessStatus=user.access_status.value,
            isAdmin=user.is_admin,
        ),
        competition=build_competition_window_response(competition_window, now=now, db_session=db_session),
        nextLockAt=next_lock_at,
        rankingPosition=get_current_user_rank(ranking_rows, user_id=user.id),
        totalPoints=total_points,
        savedMatchPredictions=int(db_session.scalar(match_prediction_count_statement) or 0),
        savedBonusPredictions=int(db_session.scalar(competition_prediction_count_statement) or 0),
        nextMatches=[
            NextMatchResponse(
                id=m.id,
                homeTeam=get_team_metadata(m.home_team_fifa_code, m.home_team_name).name,
                homeCode=get_team_metadata(m.home_team_fifa_code, m.home_team_name).code,
                homeIso2=get_team_metadata(m.home_team_fifa_code, m.home_team_name).iso2,
                homeFlag=get_team_metadata(m.home_team_fifa_code, m.home_team_name).flag,
                awayTeam=get_team_metadata(m.away_team_fifa_code, m.away_team_name).name,
                awayCode=get_team_metadata(m.away_team_fifa_code, m.away_team_name).code,
                awayIso2=get_team_metadata(m.away_team_fifa_code, m.away_team_name).iso2,
                awayFlag=get_team_metadata(m.away_team_fifa_code, m.away_team_name).flag,
                startsAt=m.starts_at.isoformat(),
                involvesBrazil=m.involves_brazil,
            )
            for m in next_matches
        ],
    )


@router.get("/predictions", response_model=MemberPredictionsResponse, status_code=status.HTTP_200_OK)
def get_predictions(
    user: User = Depends(require_approved_user),
    competition_window: CompetitionWindowSnapshot = Depends(get_competition_window_dependency),
    db_session: Session = Depends(get_db_session),
) -> MemberPredictionsResponse:
    now = utc_now()
    match_predictions_statement = (
        select(MatchPrediction)
        .where(MatchPrediction.user_id == user.id)
        .order_by(MatchPrediction.created_at.asc(), MatchPrediction.id.asc())
    )
    competition_predictions_statement = (
        select(CompetitionPrediction)
        .where(CompetitionPrediction.user_id == user.id)
        .order_by(CompetitionPrediction.created_at.asc(), CompetitionPrediction.id.asc())
    )
    match_predictions = list(db_session.scalars(match_predictions_statement).all())
    competition_predictions = list(db_session.scalars(competition_predictions_statement).all())

    comp_response = build_competition_window_response(competition_window, now=now, db_session=db_session)

    return MemberPredictionsResponse(
        competition=comp_response,
        matchPredictions=[
            MatchPredictionResponse(
                id=prediction.id,
                matchId=prediction.match_id,
                homeGoals=prediction.home_goals,
                awayGoals=prediction.away_goals,
                pointsAwarded=prediction.points_awarded,
                lockedAt=prediction.locked_at,
            )
            for prediction in match_predictions
        ],
        competitionPredictions=[
            CompetitionPredictionResponse(
                id=prediction.id,
                predictionType=prediction.prediction_type,
                selectionKey=prediction.selection_key,
                selectionLabel=prediction.selection_label,
                pointsAwarded=prediction.points_awarded,
                lockedAt=prediction.locked_at,
            )
            for prediction in competition_predictions
        ],
    )


@router.put("/predictions/matches/{match_id}", response_model=MatchPredictionResponse, status_code=status.HTTP_200_OK)
def save_match_prediction(
    match_id: UUID,
    payload: MatchPredictionRequest,
    user: User = Depends(require_approved_user),
    competition_window: CompetitionWindowSnapshot = Depends(get_competition_window_dependency),
    db_session: Session = Depends(get_db_session),
) -> MatchPredictionResponse:
    now = utc_now()
    phase_configs = _phase_config_map(db_session)
    match = get_match_by_id(db_session, match_id)
    if match is None:
        raise build_auth_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="match_not_found",
            message="Match was not found",
        )
    match_round_key = _match_round_key(match)
    if match_round_key is None:
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="prediction_window_closed",
            message="Predictions are locked",
        )
    if phase_configs:
        if _phase_locked(db_session, match_round_key, now):
            raise build_auth_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="prediction_window_closed",
                message="Predictions are locked",
            )
    elif now >= as_utc(competition_window.prediction_close_at):
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="prediction_window_closed",
            message="Predictions are locked",
        )
    prediction = get_match_prediction(db_session, user_id=user.id, match_id=match.id)
    if prediction is None:
        prediction = MatchPrediction(
            user_id=user.id,
            match_id=match.id,
            home_goals=payload.home_goals,
            away_goals=payload.away_goals,
        )
        db_session.add(prediction)
    else:
        prediction.home_goals = payload.home_goals
        prediction.away_goals = payload.away_goals
    db_session.flush()
    return MatchPredictionResponse(
        id=prediction.id,
        matchId=prediction.match_id,
        homeGoals=prediction.home_goals,
        awayGoals=prediction.away_goals,
        pointsAwarded=prediction.points_awarded,
        lockedAt=prediction.locked_at,
    )


def save_competition_prediction(
    *,
    prediction_type: PredictionType,
    payload: CompetitionPredictionRequest,
    user: User,
    competition_window: CompetitionWindowSnapshot,
    db_session: Session,
) -> CompetitionPredictionResponse:
    now = utc_now()
    phase_configs = _phase_config_map(db_session)
    if phase_configs:
        if _phase_locked(db_session, "initial_predictions", now):
            raise build_auth_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="prediction_window_closed",
                message="Predictions are locked",
            )
    elif now >= as_utc(competition_window.prediction_close_at):
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="prediction_window_closed",
            message="Predictions are locked",
        )
    prediction = get_competition_prediction(
        db_session,
        user_id=user.id,
        prediction_type=prediction_type,
    )
    if prediction is None:
        prediction = CompetitionPrediction(
            user_id=user.id,
            prediction_type=prediction_type,
            selection_key=payload.selection_key.strip(),
            selection_label=payload.selection_label.strip(),
        )
        db_session.add(prediction)
    else:
        prediction.selection_key = payload.selection_key.strip()
        prediction.selection_label = payload.selection_label.strip()
    db_session.flush()
    return CompetitionPredictionResponse(
        id=prediction.id,
        predictionType=prediction.prediction_type,
        selectionKey=prediction.selection_key,
        selectionLabel=prediction.selection_label,
        pointsAwarded=prediction.points_awarded,
        lockedAt=prediction.locked_at,
    )


@router.put("/predictions/champion", response_model=CompetitionPredictionResponse, status_code=status.HTTP_200_OK)
def save_champion_prediction(
    payload: CompetitionPredictionRequest,
    user: User = Depends(require_approved_user),
    competition_window: CompetitionWindowSnapshot = Depends(get_competition_window_dependency),
    db_session: Session = Depends(get_db_session),
) -> CompetitionPredictionResponse:
    return save_competition_prediction(
        prediction_type=PredictionType.CHAMPION,
        payload=payload,
        user=user,
        competition_window=competition_window,
        db_session=db_session,
    )


@router.put("/predictions/top-scorer", response_model=CompetitionPredictionResponse, status_code=status.HTTP_200_OK)
def save_top_scorer_prediction(
    payload: CompetitionPredictionRequest,
    user: User = Depends(require_approved_user),
    competition_window: CompetitionWindowSnapshot = Depends(get_competition_window_dependency),
    db_session: Session = Depends(get_db_session),
) -> CompetitionPredictionResponse:
    return save_competition_prediction(
        prediction_type=PredictionType.TOP_SCORER,
        payload=payload,
        user=user,
        competition_window=competition_window,
        db_session=db_session,
    )


@router.get("/ranking", response_model=RankingResponse, status_code=status.HTTP_200_OK)
def get_ranking(
    user: User = Depends(require_approved_user),
    db_session: Session = Depends(get_db_session),
) -> RankingResponse:
    rows = build_ranking_rows(db_session)
    return RankingResponse(
        rows=[
            RankingRowResponse(
                rank=row.rank,
                userId=row.user_id,
                fullName=row.full_name,
                totalPoints=row.total_points,
                matchPoints=row.match_points,
                exactPoints=row.exact_points,
                resultPoints=row.result_points,
                brazilPoints=row.brazil_points,
                bonusPoints=row.bonus_points,
            )
            for row in rows
        ],
        currentUserRank=get_current_user_rank(rows, user_id=user.id),
        currentUserBreakdown=build_current_user_breakdown(db_session, user_id=user.id),
    )


@router.get("/explore", response_model=ExploreResponse, status_code=status.HTTP_200_OK)
def get_explore(
    user: User = Depends(require_approved_user),
    competition_window: CompetitionWindowSnapshot = Depends(get_competition_window_dependency),
    db_session: Session = Depends(get_db_session),
) -> ExploreResponse:
    now = utc_now()
    del competition_window
    phase_configs = _phase_config_map(db_session)
    match_predictions = list(
        db_session.scalars(
            select(MatchPrediction)
            .join(User, User.id == MatchPrediction.user_id)
            .join(Match, Match.id == MatchPrediction.match_id)
            .options(
                joinedload(MatchPrediction.user),
                joinedload(MatchPrediction.match),
            )
            .where(User.access_status == AccessStatus.APPROVED, User.is_active.is_(True))
            .order_by(
                Match.starts_at.asc(),
                Match.id.asc(),
                MatchPrediction.created_at.asc(),
                MatchPrediction.id.asc(),
            )
        ).all()
    )
    competition_predictions = list(
        db_session.scalars(
            select(CompetitionPrediction)
            .join(User, User.id == CompetitionPrediction.user_id)
            .options(joinedload(CompetitionPrediction.user))
            .where(User.access_status == AccessStatus.APPROVED, User.is_active.is_(True))
            .order_by(
                CompetitionPrediction.created_at.asc(),
                CompetitionPrediction.id.asc(),
            )
        ).all()
    )

    grouped_predictions: dict[UUID, list[MatchPrediction]] = defaultdict(list)
    ordered_matches: dict[UUID, Match] = {}
    for prediction in match_predictions:
        match = prediction.match
        ordered_matches[match.id] = match
        if _is_explore_match_public(
            match,
            now=now,
            db_session=db_session,
            phase_configs=phase_configs,
        ):
            grouped_predictions[match.id].append(prediction)

    sorted_match_ids = sorted(
        grouped_predictions,
        key=lambda match_id: (
            as_utc(ordered_matches[match_id].starts_at),
            ordered_matches[match_id].id,
        ),
    )

    match_groups = [
        _build_explore_match_group_response(
            match=ordered_matches[match_id],
            predictions=grouped_predictions[match_id],
        )
        for match_id in sorted_match_ids
    ]
    flat_match_predictions = [
        prediction
        for match_id in sorted_match_ids
        for prediction in grouped_predictions[match_id]
    ]
    total_match_ids = {prediction.match_id for prediction in match_predictions}
    public_match_ids = set(sorted_match_ids)
    if not public_match_ids:
        explore_state = "locked"
    elif public_match_ids == total_match_ids:
        explore_state = "released"
    else:
        explore_state = "partial"

    return ExploreResponse(
        exploreState=explore_state,
        exploreReleased=explore_state == "released",
        matchGroups=match_groups,
        matchPredictions=[
            build_explore_match_prediction_response(prediction)
            for prediction in flat_match_predictions
        ],
        competitionPredictions=[
            build_explore_competition_prediction_response(prediction)
            for prediction in competition_predictions
        ],
    )


@router.get("/results", response_model=MemberResultsScreenDto, status_code=status.HTTP_200_OK)
def get_results_screen(
    user: User = Depends(require_approved_user),
    db_session: Session = Depends(get_db_session),
) -> MemberResultsScreenDto:
    return FrontendContractService(db_session).build_member_results(user=user)


@router.get("/bracket", response_model=MemberBracketScreenDto, status_code=status.HTTP_200_OK)
def get_bracket_screen(
    user: User = Depends(require_approved_user),
    db_session: Session = Depends(get_db_session),
) -> MemberBracketScreenDto:
    return FrontendContractService(db_session).build_member_bracket(user=user)


@router.get("/available-teams", status_code=status.HTTP_200_OK)
def get_available_teams(user: User = Depends(require_approved_user)) -> list[dict]:
    return _load_teams()


@router.get("/available-players", status_code=status.HTTP_200_OK)
def get_available_players(user: User = Depends(require_approved_user)) -> list[dict]:
    return _load_players()


# ── Phase helpers ─────────────────────────────────────────────────────────────

PHASE_LOCK_OFFSET = timedelta(minutes=30)

_ROUND_CONFIG_KEYS = ["round1", "round2", "round3", "roundOf32", "roundOf16", "quarterFinal", "semiFinal", "final"]

_ROUND_PHASES = [
    ("round1", CompetitionPhase.GROUP_STAGE, 1),
    ("round2", CompetitionPhase.GROUP_STAGE, 2),
    ("round3", CompetitionPhase.GROUP_STAGE, 3),
    ("roundOf32", CompetitionPhase.ROUND_OF_32, None),
    ("roundOf16", CompetitionPhase.ROUND_OF_16, None),
    ("quarterFinal", CompetitionPhase.QUARTER_FINAL, None),
    ("semiFinal", CompetitionPhase.SEMI_FINAL, None),
    ("final", CompetitionPhase.FINAL, None),
]


def _phase_config_map(db_session: Session) -> dict[str, CompetitionPhaseConfig]:
    return {
        config.phase_key: config
        for config in list_active_competition_phase_configs(db_session)
    }


def _next_lock_at_from_configs(
    phase_configs: dict[str, CompetitionPhaseConfig],
    now: datetime,
) -> datetime | None:
    ordered = sorted(phase_configs.values(), key=lambda item: (item.sort_order, item.lock_at, item.phase_key))
    for config in ordered:
        if config.is_force_locked:
            continue
        lock_at = as_utc(config.lock_at)
        if now < lock_at:
            return lock_at
    return None


def _phase_locked(
    db_session: Session,
    phase_key: str,
    now: datetime,
    fallback_bitmask: int | None = None,
) -> bool:
    phase_configs = _phase_config_map(db_session)
    config = phase_configs.get(phase_key)
    if config is not None:
        return config.is_force_locked or now >= as_utc(config.lock_at)

    if fallback_bitmask is None:
        return False

    fallback_keys = ["initial_predictions", *_ROUND_CONFIG_KEYS]
    try:
        idx = fallback_keys.index(phase_key)
    except ValueError:
        return False
    return bool(fallback_bitmask & (1 << idx))


def _match_round_key(match: Match) -> str | None:
    if match.phase == CompetitionPhase.GROUP_STAGE:
        return {1: "round1", 2: "round2", 3: "round3"}.get(match.stage_round)
    mapping = {
        CompetitionPhase.ROUND_OF_32: "roundOf32",
        CompetitionPhase.ROUND_OF_16: "roundOf16",
        CompetitionPhase.QUARTER_FINAL: "quarterFinal",
        CompetitionPhase.SEMI_FINAL: "semiFinal",
        CompetitionPhase.FINAL: "final",
    }
    return mapping.get(match.phase)


def _phase_lock_time(db_session: Session, phase: CompetitionPhase, stage_round: int | None) -> datetime | None:
    """Return the lock time for a phase = first match starts_at - 30m."""
    stmt = select(Match.starts_at).where(Match.phase == phase)
    if stage_round is not None:
        stmt = stmt.where(Match.stage_round == stage_round)
    stmt = stmt.where(
        Match.home_team_name != "TBD",
        Match.away_team_name != "TBD",
    ).order_by(Match.starts_at.asc()).limit(1)
    first = db_session.scalar(stmt)
    if first is None:
        return None
    return as_utc(first) - PHASE_LOCK_OFFSET


def _compute_phase_locks_from_configs(
    phase_configs: dict[str, CompetitionPhaseConfig],
    now: datetime,
) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for key in ["initial_predictions", *_ROUND_CONFIG_KEYS]:
        config = phase_configs.get(key)
        if config is None:
            result[key] = False
            continue
        result[key] = config.is_force_locked or now >= as_utc(config.lock_at)
    return result


def _compute_phase_locks(
    db_session: Session,
    now: datetime,
    force_bitmask: int | None,
) -> dict[str, bool]:
    """Return a dict key→is_locked for each round."""
    phase_configs = _phase_config_map(db_session)
    if phase_configs:
        result = _compute_phase_locks_from_configs(phase_configs, now)
        return {key: result.get(key, False) for key, _, _ in _ROUND_PHASES}

    result: dict[str, bool] = {}
    for idx, (key, phase, stage_round) in enumerate(_ROUND_PHASES):
        force_bit = bool(force_bitmask and (force_bitmask & (1 << idx)))
        lock_time = _phase_lock_time(db_session, phase, stage_round)
        auto_locked = lock_time is not None and now >= lock_time
        result[key] = force_bit or auto_locked
    return result


def _compute_explore_open(phase_locks: dict[str, bool]) -> dict[str, bool]:
    """Explore for round N opens once round N is locked (additive)."""
    explore: dict[str, bool] = {}
    unlocked_prefix = False
    for key in _ROUND_CONFIG_KEYS:
        locked = phase_locks.get(key, False)
        unlocked_prefix = unlocked_prefix or locked
        explore[key] = unlocked_prefix
    return explore


def _compute_explore_open_from_configs(
    phase_configs: dict[str, CompetitionPhaseConfig],
    now: datetime,
) -> dict[str, bool]:
    """Explore visibility follows exploreAt for each round independently."""
    explore: dict[str, bool] = {}
    for key in ["initial_predictions", *_ROUND_CONFIG_KEYS]:
        config = phase_configs.get(key)
        if config is None:
            explore[key] = False
            continue
        explore[key] = config.is_force_locked or now >= as_utc(config.explore_at)
    return explore


# ── Phase matches response models ────────────────────────────────────────────

class PhaseMatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    homeTeam: str
    awayTeam: str
    homeCode: str | None
    homeIso2: str | None
    homeFlag: str
    awayCode: str | None
    awayIso2: str | None
    awayFlag: str
    groupName: str | None
    startsAt: str
    involvesBrazil: bool
    status: str
    officialHomeGoals: int | None
    officialAwayGoals: int | None
    predictedHomeGoals: int | None
    predictedAwayGoals: int | None
    pointsAwarded: int | None


class PhaseRoundResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    phase: str
    stageRound: int | None
    locked: bool
    exploreOpen: bool
    lockTime: str | None
    matches: list[PhaseMatchResponse]


class PhaseScreenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rounds: list[PhaseRoundResponse]


_ROUND_LABELS = {
    "round1": "Grupos · Rodada 1",
    "round2": "Grupos · Rodada 2",
    "round3": "Grupos · Rodada 3",
    "roundOf32": "16 avos",
    "roundOf16": "Oitavas",
    "quarterFinal": "Quartas",
    "semiFinal": "Semifinal",
    "final": "Final",
}


@router.get("/phase-screen", response_model=PhaseScreenResponse, status_code=status.HTTP_200_OK)
def get_phase_screen(
    user: User = Depends(require_approved_user),
    db_session: Session = Depends(get_db_session),
) -> PhaseScreenResponse:
    now = utc_now()
    phase_configs = _phase_config_map(db_session)
    if phase_configs:
        phase_locks = _compute_phase_locks_from_configs(phase_configs, now)
        explore_open = _compute_explore_open_from_configs(phase_configs, now)
    else:
        # Load active competition window for force_locked_phases bitmask
        cw = db_session.scalar(select(CompetitionWindow).where(CompetitionWindow.is_active.is_(True)))
        bitmask = cw.force_locked_phases if cw else None

        phase_locks = _compute_phase_locks(db_session, now, bitmask)
        explore_open = _compute_explore_open(phase_locks)

    # Load all match predictions for this user
    predictions_stmt = select(MatchPrediction).where(MatchPrediction.user_id == user.id)
    preds_by_match: dict[UUID, MatchPrediction] = {
        p.match_id: p for p in db_session.scalars(predictions_stmt).all()
    }

    rounds: list[PhaseRoundResponse] = []
    for key, phase, stage_round in _ROUND_PHASES:
        # Load matches for this round
        stmt = select(Match).where(Match.phase == phase)
        if stage_round is not None:
            stmt = stmt.where(Match.stage_round == stage_round)
        stmt = stmt.order_by(Match.starts_at.asc())
        matches = list(db_session.scalars(stmt).all())

        if phase_configs:
            lock_time_value = phase_configs.get(key).lock_at if phase_configs.get(key) is not None else None
            lock_time = as_utc(lock_time_value) if lock_time_value is not None else None
        else:
            lock_time = _phase_lock_time(db_session, phase, stage_round)
        locked = phase_locks[key]

        match_responses: list[PhaseMatchResponse] = []
        for m in matches:
            pred = preds_by_match.get(m.id)
            home_team = get_team_metadata(m.home_team_fifa_code, m.home_team_name)
            away_team = get_team_metadata(m.away_team_fifa_code, m.away_team_name)
            match_responses.append(PhaseMatchResponse(
                id=m.id,
                homeTeam=home_team.name,
                awayTeam=away_team.name,
                homeCode=home_team.code,
                homeIso2=home_team.iso2,
                homeFlag=home_team.flag,
                awayCode=away_team.code,
                awayIso2=away_team.iso2,
                awayFlag=away_team.flag,
                groupName=m.group_name,
                startsAt=m.starts_at.isoformat(),
                involvesBrazil=m.involves_brazil,
                status=m.status,
                officialHomeGoals=m.official_home_goals,
                officialAwayGoals=m.official_away_goals,
                predictedHomeGoals=pred.home_goals if pred else None,
                predictedAwayGoals=pred.away_goals if pred else None,
                pointsAwarded=pred.points_awarded if pred else None,
            ))

        rounds.append(PhaseRoundResponse(
            key=key,
            label=_ROUND_LABELS[key],
            phase=phase.value,
            stageRound=stage_round,
            locked=locked,
            exploreOpen=explore_open[key],
            lockTime=lock_time.isoformat() if lock_time else None,
            matches=match_responses,
        ))

    return PhaseScreenResponse(rounds=rounds)


# ── Standings ─────────────────────────────────────────────────────────────────

class StandingEntryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    teamCode: str
    teamName: str
    teamIso2: str | None
    teamFlag: str
    played: int
    won: int
    drawn: int
    lost: int
    goalsFor: int
    goalsAgainst: int
    goalDiff: int
    points: int


class GroupStandingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group: str
    entries: list[StandingEntryResponse]


class StandingsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    groups: list[GroupStandingResponse]


@router.get("/standings", response_model=StandingsResponse, status_code=status.HTTP_200_OK)
def get_standings(
    user: User = Depends(require_approved_user),
    db_session: Session = Depends(get_db_session),
) -> StandingsResponse:
    stmt = (
        select(Match)
        .where(Match.phase == CompetitionPhase.GROUP_STAGE)
        .order_by(Match.group_name.asc(), Match.starts_at.asc())
    )
    group_matches = list(db_session.scalars(stmt).all())

    # Aggregate per group
    from collections import defaultdict

    # team_data[group][team_code] = {name, p, w, d, l, gf, ga}
    team_data: dict[str, dict[str, dict]] = defaultdict(dict)

    # Seed teams from matches so even 0-played teams appear
    for m in group_matches:
        grp = m.group_name or "?"
        for code, name in [
            (m.home_team_fifa_code or m.home_team_name, m.home_team_name),
            (m.away_team_fifa_code or m.away_team_name, m.away_team_name),
        ]:
            if code not in team_data[grp]:
                team = get_team_metadata(code, name)
                team_data[grp][code] = {
                    "name": team.name,
                    "iso2": team.iso2,
                    "flag": team.flag,
                    "p": 0,
                    "w": 0,
                    "d": 0,
                    "l": 0,
                    "gf": 0,
                    "ga": 0,
                }

    # Apply finished results
    for m in group_matches:
        if m.official_home_goals is None or m.official_away_goals is None:
            continue
        grp = m.group_name or "?"
        hg = m.official_home_goals
        ag = m.official_away_goals
        hc = m.home_team_fifa_code or m.home_team_name
        ac = m.away_team_fifa_code or m.away_team_name

        for code in (hc, ac):
            team_data[grp][code]["p"] += 1
        team_data[grp][hc]["gf"] += hg
        team_data[grp][hc]["ga"] += ag
        team_data[grp][ac]["gf"] += ag
        team_data[grp][ac]["ga"] += hg

        if hg > ag:
            team_data[grp][hc]["w"] += 1
            team_data[grp][ac]["l"] += 1
        elif hg < ag:
            team_data[grp][ac]["w"] += 1
            team_data[grp][hc]["l"] += 1
        else:
            team_data[grp][hc]["d"] += 1
            team_data[grp][ac]["d"] += 1

    groups: list[GroupStandingResponse] = []
    for grp in sorted(team_data.keys()):
        entries = []
        for code, d in team_data[grp].items():
            pts = d["w"] * 3 + d["d"]
            gd = d["gf"] - d["ga"]
            entries.append(StandingEntryResponse(
                teamCode=code,
                teamName=d["name"],
                teamIso2=d["iso2"],
                teamFlag=d["flag"],
                played=d["p"],
                won=d["w"],
                drawn=d["d"],
                lost=d["l"],
                goalsFor=d["gf"],
                goalsAgainst=d["ga"],
                goalDiff=gd,
                points=pts,
            ))
        # Sort: pts desc, gd desc, gf desc
        entries.sort(key=lambda e: (-e.points, -e.goalDiff, -e.goalsFor))
        groups.append(GroupStandingResponse(group=grp, entries=entries))

    return StandingsResponse(groups=groups)
