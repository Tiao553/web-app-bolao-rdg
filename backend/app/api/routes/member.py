from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas.frontend import MemberBracketScreenDto, MemberResultsScreenDto
from app.core.security import build_auth_error, require_approved_user
from app.models.schema import (
    CompetitionPrediction,
    MatchPrediction,
    PredictionType,
    User,
)
from app.repositories.queries import (
    CompetitionWindowSnapshot,
    get_competition_prediction,
    get_competition_window_dependency,
    get_db_session,
    get_match_by_id,
    get_match_prediction,
    ranking_users_select,
    visible_competition_predictions_select,
    visible_match_predictions_select,
)
from app.services.frontend_contract_service import FrontendContractService

router = APIRouter(prefix="/api/member", tags=["member"])


@dataclass(frozen=True, slots=True)
class RankingRowData:
    rank: int
    user_id: UUID
    full_name: str
    total_points: int
    match_points: int
    bonus_points: int


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


class DashboardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: DashboardUserResponse
    competition: CompetitionWindowResponse
    rankingPosition: int | None
    totalPoints: int
    savedMatchPredictions: int
    savedBonusPredictions: int


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
    bonusPoints: int


class RankingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[RankingRowResponse]
    currentUserRank: int | None


class ExploreMatchPredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    userId: UUID
    userName: str
    matchId: UUID
    homeGoals: int
    awayGoals: int
    pointsAwarded: int | None


class ExploreCompetitionPredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    userId: UUID
    userName: str
    predictionType: PredictionType
    selectionKey: str
    selectionLabel: str
    pointsAwarded: int | None


class ExploreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exploreReleased: bool
    matchPredictions: list[ExploreMatchPredictionResponse]
    competitionPredictions: list[ExploreCompetitionPredictionResponse]


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
) -> CompetitionWindowResponse:
    return CompetitionWindowResponse(
        predictionCloseAt=as_utc(competition_window.prediction_close_at),
        exploreReleaseAt=as_utc(competition_window.explore_release_at),
        predictionLocked=now >= as_utc(competition_window.prediction_close_at),
        exploreReleased=now >= as_utc(competition_window.explore_release_at),
    )


def build_ranking_rows(db_session: Session) -> list[RankingRowData]:
    approved_users = list(db_session.scalars(ranking_users_select()).all())

    match_points_statement = (
        select(
            MatchPrediction.user_id,
            func.coalesce(func.sum(MatchPrediction.points_awarded), 0),
        )
        .group_by(MatchPrediction.user_id)
    )
    bonus_points_statement = (
        select(
            CompetitionPrediction.user_id,
            func.coalesce(func.sum(CompetitionPrediction.points_awarded), 0),
        )
        .group_by(CompetitionPrediction.user_id)
    )

    match_points_by_user = {
        user_id: int(total_points)
        for user_id, total_points in db_session.execute(match_points_statement).all()
    }
    bonus_points_by_user = {
        user_id: int(total_points)
        for user_id, total_points in db_session.execute(bonus_points_statement).all()
    }

    sorted_users = sorted(
        approved_users,
        key=lambda item: (
            -(match_points_by_user.get(item.id, 0) + bonus_points_by_user.get(item.id, 0)),
            item.created_at,
            str(item.id),
        ),
    )

    rows: list[RankingRowData] = []
    for index, approved_user in enumerate(sorted_users, start=1):
        match_points = match_points_by_user.get(approved_user.id, 0)
        bonus_points = bonus_points_by_user.get(approved_user.id, 0)
        rows.append(
            RankingRowData(
                rank=index,
                user_id=approved_user.id,
                full_name=approved_user.full_name,
                total_points=match_points + bonus_points,
                match_points=match_points,
                bonus_points=bonus_points,
            )
        )
    return rows


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

    return DashboardResponse(
        user=DashboardUserResponse(
            id=user.id,
            email=user.email,
            name=user.full_name,
            accessStatus=user.access_status.value,
            isAdmin=user.is_admin,
        ),
        competition=build_competition_window_response(competition_window, now=now),
        rankingPosition=get_current_user_rank(ranking_rows, user_id=user.id),
        totalPoints=total_points,
        savedMatchPredictions=int(db_session.scalar(match_prediction_count_statement) or 0),
        savedBonusPredictions=int(db_session.scalar(competition_prediction_count_statement) or 0),
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

    return MemberPredictionsResponse(
        competition=build_competition_window_response(competition_window, now=now),
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
    if now >= as_utc(competition_window.prediction_close_at):
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="prediction_window_closed",
            message="Predictions are locked",
        )
    match = get_match_by_id(db_session, match_id)
    if match is None:
        raise build_auth_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="match_not_found",
            message="Match was not found",
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
    if now >= as_utc(competition_window.prediction_close_at):
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
                bonusPoints=row.bonus_points,
            )
            for row in rows
        ],
        currentUserRank=get_current_user_rank(rows, user_id=user.id),
    )


@router.get("/explore", response_model=ExploreResponse, status_code=status.HTTP_200_OK)
def get_explore(
    user: User = Depends(require_approved_user),
    competition_window: CompetitionWindowSnapshot = Depends(get_competition_window_dependency),
    db_session: Session = Depends(get_db_session),
) -> ExploreResponse:
    now = utc_now()
    explore_released = now >= as_utc(competition_window.explore_release_at)
    match_predictions = list(
        db_session.scalars(
            visible_match_predictions_select(
                viewer=user,
                explore_released=explore_released,
            )
        ).all()
    )
    competition_predictions = list(
        db_session.scalars(
            visible_competition_predictions_select(
                viewer=user,
                explore_released=explore_released,
            )
        ).all()
    )

    return ExploreResponse(
        exploreReleased=explore_released,
        matchPredictions=[
            ExploreMatchPredictionResponse(
                userId=prediction.user_id,
                userName=prediction.user.full_name,
                matchId=prediction.match_id,
                homeGoals=prediction.home_goals,
                awayGoals=prediction.away_goals,
                pointsAwarded=prediction.points_awarded,
            )
            for prediction in match_predictions
        ],
        competitionPredictions=[
            ExploreCompetitionPredictionResponse(
                userId=prediction.user_id,
                userName=prediction.user.full_name,
                predictionType=prediction.prediction_type,
                selectionKey=prediction.selection_key,
                selectionLabel=prediction.selection_label,
                pointsAwarded=prediction.points_awarded,
            )
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
