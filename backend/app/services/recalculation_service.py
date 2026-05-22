from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.bracket import (
    KnockoutMatch,
    QualifiedThirdPlaceTeam,
    allocate_third_place_slots,
    propagate_knockout_results,
)
from app.domain.scoring import (
    MatchScoreInput,
    OfficialMatchResult,
    ScoreRules,
    score_champion_prediction,
    score_match_prediction,
    score_top_scorer_prediction,
)
from app.domain.standings import (
    GroupMatchResult,
    GroupTeamSeed,
    TeamStanding,
    build_all_group_standings,
    select_best_third_placed_teams,
)
from app.models.schema import (
    AccessStatus,
    CompetitionPhase,
    CompetitionPrediction,
    Match,
    MatchPrediction,
    PredictionType,
    User,
)


class RecalculationStageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    updated_count: int
    skipped_count: int
    notes: str | None = None


class RankingSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int
    user_id: UUID
    full_name: str
    total_points: int
    match_points: int
    bonus_points: int


class RecalculationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executed_at: datetime
    standings: RecalculationStageSummary
    bracket: RecalculationStageSummary
    match_points: RecalculationStageSummary
    competition_points: RecalculationStageSummary
    ranking: RecalculationStageSummary
    ranking_rows: list[RankingSnapshotRow]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_score_rules() -> ScoreRules:
    from app.core.config import get_settings

    settings = get_settings()
    return ScoreRules.from_settings(settings.scoring)


def _match_status_is_terminal(match: Match) -> bool:
    return match.status in {"FT", "AET", "PEN"}


def _build_group_seeds(matches: Iterable[Match]) -> tuple[GroupTeamSeed, ...]:
    seeds: dict[tuple[str, str], GroupTeamSeed] = {}
    for match in matches:
        if match.group_name is None:
            continue
        if match.home_team_fifa_code is not None:
            seeds[(match.group_name, match.home_team_fifa_code)] = GroupTeamSeed(
                group_name=match.group_name,
                team_key=match.home_team_fifa_code,
            )
        if match.away_team_fifa_code is not None:
            seeds[(match.group_name, match.away_team_fifa_code)] = GroupTeamSeed(
                group_name=match.group_name,
                team_key=match.away_team_fifa_code,
            )
    return tuple(seeds.values())


def _build_group_results(matches: Iterable[Match]) -> tuple[GroupMatchResult, ...]:
    results: list[GroupMatchResult] = []
    for match in matches:
        if match.group_name is None:
            continue
        if not _match_status_is_terminal(match):
            continue
        if match.official_home_goals is None or match.official_away_goals is None:
            continue
        if match.home_team_fifa_code is None or match.away_team_fifa_code is None:
            continue
        results.append(
            GroupMatchResult(
                group_name=match.group_name,
                home_team_key=match.home_team_fifa_code,
                away_team_key=match.away_team_fifa_code,
                home_goals=match.official_home_goals,
                away_goals=match.official_away_goals,
            )
        )
    return tuple(results)


def recalculate_standings(db_session: Session) -> tuple[RecalculationStageSummary, dict[str, tuple[TeamStanding, ...]]]:
    matches = list(
        db_session.scalars(
            select(Match).where(Match.phase == CompetitionPhase.GROUP_STAGE)
        ).all()
    )
    seeds = _build_group_seeds(matches)
    results = _build_group_results(matches)
    if len(seeds) == 0 or len(results) == 0:
        return (
            RecalculationStageSummary(
                status="limited",
                updated_count=0,
                skipped_count=0,
                notes="Group seeds or results are incomplete for standings computation",
            ),
            {},
        )
    standings_by_group = build_all_group_standings(seeds, results)
    return (
        RecalculationStageSummary(
            status="computed",
            updated_count=sum(len(rows) for rows in standings_by_group.values()),
            skipped_count=0,
            notes="Computed in memory from terminal group-stage matches",
        ),
        standings_by_group,
    )


def _build_knockout_matches(matches: Iterable[Match]) -> tuple[KnockoutMatch, ...]:
    knockout: list[KnockoutMatch] = []
    for match in matches:
        if match.bracket_slot is None:
            continue
        if match.phase == CompetitionPhase.GROUP_STAGE:
            continue
        knockout.append(
            KnockoutMatch(
                slot=match.bracket_slot,
                home_team_key=match.home_team_fifa_code,
                away_team_key=match.away_team_fifa_code,
                feeder_home_key=match.feeder_home_key,
                feeder_away_key=match.feeder_away_key,
                winner_team_key=match.winner_team_name,
            )
        )
    return tuple(knockout)


def _resolve_group_slot_team(
    feeder_key: str | None,
    standings_by_group: Mapping[str, tuple[TeamStanding, ...]],
) -> str | None:
    if feeder_key is None or ":" not in feeder_key:
        return None
    slot_type, group_name = feeder_key.split(":", 1)
    rows = standings_by_group.get(group_name)
    if not rows:
        return None
    if slot_type == "WINNER" and len(rows) >= 1:
        return rows[0].team_key
    if slot_type == "RUNNER_UP" and len(rows) >= 2:
        return rows[1].team_key
    return None


def recalculate_bracket(
    db_session: Session,
    standings_by_group: Mapping[str, tuple[TeamStanding, ...]],
) -> RecalculationStageSummary:
    all_matches = list(db_session.scalars(select(Match)).all())
    qualified_third_rows = select_best_third_placed_teams(
        row
        for rows in standings_by_group.values()
        if len(rows) >= 3
        for row in rows[2:3]
    )
    updated_count = 0
    if len(qualified_third_rows) == 8:
        allocations = allocate_third_place_slots(
            QualifiedThirdPlaceTeam(group_name=row.group_name, team_key=row.team_key)
            for row in qualified_third_rows
        )
        by_slot = {match.bracket_slot: match for match in all_matches if match.bracket_slot is not None}
        for allocation in allocations:
            match = by_slot.get(allocation.slot)
            if match is None:
                continue
            if match.away_team_fifa_code != allocation.team_key:
                match.away_team_fifa_code = allocation.team_key
                updated_count += 1
                db_session.add(match)
    for match in all_matches:
        home_group_team = _resolve_group_slot_team(match.feeder_home_key, standings_by_group)
        away_group_team = _resolve_group_slot_team(match.feeder_away_key, standings_by_group)
        if home_group_team is not None and match.home_team_fifa_code != home_group_team:
            match.home_team_fifa_code = home_group_team
            updated_count += 1
            db_session.add(match)
        if away_group_team is not None and match.away_team_fifa_code != away_group_team:
            match.away_team_fifa_code = away_group_team
            updated_count += 1
            db_session.add(match)
    knockout_matches = _build_knockout_matches(all_matches)
    propagated = propagate_knockout_results(knockout_matches)
    propagated_by_slot = {match.slot: match for match in propagated}
    for match in all_matches:
        if match.bracket_slot is None:
            continue
        propagated_match = propagated_by_slot.get(match.bracket_slot)
        if propagated_match is None:
            continue
        if propagated_match.home_team_key is not None and match.home_team_fifa_code != propagated_match.home_team_key:
            match.home_team_fifa_code = propagated_match.home_team_key
            updated_count += 1
            db_session.add(match)
        if propagated_match.away_team_key is not None and match.away_team_fifa_code != propagated_match.away_team_key:
            match.away_team_fifa_code = propagated_match.away_team_key
            updated_count += 1
            db_session.add(match)
    db_session.flush()
    return RecalculationStageSummary(
        status="computed",
        updated_count=updated_count,
        skipped_count=0,
        notes="Bracket slots and knockout propagation were computed in memory and mirrored into match records",
    )


def recalculate_match_prediction_points(
    db_session: Session,
    *,
    match_id: UUID | None = None,
) -> RecalculationStageSummary:
    rules = get_score_rules()
    statement = select(Match).where(
        Match.status.in_(("FT", "AET", "PEN")),
        Match.official_home_goals.is_not(None),
        Match.official_away_goals.is_not(None),
    )
    if match_id is not None:
        statement = statement.where(Match.id == match_id)
    matches = list(db_session.scalars(statement).all())
    updated_count = 0
    skipped_count = 0
    for match in matches:
        predictions = list(
            db_session.scalars(
                select(MatchPrediction).where(MatchPrediction.match_id == match.id)
            ).all()
        )
        official = OfficialMatchResult(
            home_goals=int(match.official_home_goals or 0),
            away_goals=int(match.official_away_goals or 0),
            involves_brazil=match.involves_brazil,
        )
        for prediction in predictions:
            points = score_match_prediction(
                MatchScoreInput(
                    home_goals=prediction.home_goals,
                    away_goals=prediction.away_goals,
                ),
                official,
                rules,
            )
            if prediction.points_awarded == points:
                skipped_count += 1
                continue
            prediction.points_awarded = points
            prediction.locked_at = prediction.locked_at or match.starts_at
            db_session.add(prediction)
            updated_count += 1
    db_session.flush()
    return RecalculationStageSummary(
        status="completed",
        updated_count=updated_count,
        skipped_count=skipped_count,
        notes="Recomputed match prediction points from official scores",
    )


def recalculate_competition_prediction_points(
    db_session: Session,
    *,
    champion_selection_key: str | None = None,
    top_scorer_selection_keys: set[str] | None = None,
) -> RecalculationStageSummary:
    rules = get_score_rules()
    predictions = list(db_session.scalars(select(CompetitionPrediction)).all())
    updated_count = 0
    skipped_count = 0
    for prediction in predictions:
        if prediction.prediction_type is PredictionType.CHAMPION:
            next_points = score_champion_prediction(
                prediction.selection_key,
                champion_selection_key,
                rules,
            )
        else:
            next_points = score_top_scorer_prediction(
                prediction.selection_key,
                top_scorer_selection_keys or set(),
                rules,
            )
        if prediction.points_awarded == next_points:
            skipped_count += 1
            continue
        prediction.points_awarded = next_points
        db_session.add(prediction)
        updated_count += 1
    db_session.flush()
    return RecalculationStageSummary(
        status="completed",
        updated_count=updated_count,
        skipped_count=skipped_count,
        notes="Recomputed champion and top-scorer prediction points",
    )


def build_ranking_rows(db_session: Session) -> list[RankingSnapshotRow]:
    approved_users = list(
        db_session.scalars(
            select(User)
            .where(User.access_status == AccessStatus.APPROVED, User.is_active.is_(True))
            .order_by(User.created_at.asc(), User.id.asc())
        ).all()
    )
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
    rows: list[RankingSnapshotRow] = []
    for index, user in enumerate(sorted_users, start=1):
        match_points = match_points_by_user.get(user.id, 0)
        bonus_points = bonus_points_by_user.get(user.id, 0)
        rows.append(
            RankingSnapshotRow(
                rank=index,
                user_id=user.id,
                full_name=user.full_name,
                total_points=match_points + bonus_points,
                match_points=match_points,
                bonus_points=bonus_points,
            )
        )
    return rows


def recalculate_ranking(db_session: Session) -> tuple[RecalculationStageSummary, list[RankingSnapshotRow]]:
    rows = build_ranking_rows(db_session)
    return (
        RecalculationStageSummary(
            status="computed",
            updated_count=len(rows),
            skipped_count=0,
            notes="Ranking snapshots were computed in memory because no ranking table exists yet",
        ),
        rows,
    )


def recalculate_competition_state(
    db_session: Session,
    *,
    champion_selection_key: str | None = None,
    top_scorer_selection_keys: set[str] | None = None,
) -> RecalculationSummary:
    standings_summary, standings_by_group = recalculate_standings(db_session)
    bracket_summary = recalculate_bracket(db_session, standings_by_group)
    match_points_summary = recalculate_match_prediction_points(db_session)
    competition_points_summary = recalculate_competition_prediction_points(
        db_session,
        champion_selection_key=champion_selection_key,
        top_scorer_selection_keys=top_scorer_selection_keys,
    )
    ranking_summary, ranking_rows = recalculate_ranking(db_session)
    return RecalculationSummary(
        executed_at=utc_now(),
        standings=standings_summary,
        bracket=bracket_summary,
        match_points=match_points_summary,
        competition_points=competition_points_summary,
        ranking=ranking_summary,
        ranking_rows=ranking_rows,
    )


def recalculate_for_match(db_session: Session, *, match_id: UUID) -> RecalculationSummary:
    standings_summary, standings_by_group = recalculate_standings(db_session)
    bracket_summary = recalculate_bracket(db_session, standings_by_group)
    match_points_summary = recalculate_match_prediction_points(db_session, match_id=match_id)
    competition_points_summary = recalculate_competition_prediction_points(db_session)
    ranking_summary, ranking_rows = recalculate_ranking(db_session)
    return RecalculationSummary(
        executed_at=utc_now(),
        standings=standings_summary,
        bracket=bracket_summary,
        match_points=match_points_summary,
        competition_points=competition_points_summary,
        ranking=ranking_summary,
        ranking_rows=ranking_rows,
    )


def recalculate_from_sync_request(db_session: Session, request: Any) -> None:
    top_scorer_keys = {
        scorer.player_key for scorer in getattr(request, "top_scorers", ())
    }
    champion_key = None
    final_match = db_session.scalar(
        select(Match).where(Match.phase == CompetitionPhase.FINAL)
    )
    if final_match is not None and final_match.winner_team_name is not None:
        champion_key = final_match.winner_team_name
    recalculate_competition_state(
        db_session,
        champion_selection_key=champion_key,
        top_scorer_selection_keys=top_scorer_keys,
    )
