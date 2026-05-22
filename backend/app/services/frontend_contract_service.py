from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.frontend import (
    AdminDashboardScreenDto,
    AdminIntegrationScreenDto,
    AdminMatchesScreenDto,
    AdminMatchRowDto,
    AdminPlayerRowDto,
    AdminPlayersScreenDto,
    AdminSettingsScreenDto,
    AdminUserCountsDto,
    BracketMatchDto,
    BracketThirdPlaceSlotDto,
    MatchStatusCountsDto,
    MemberBracketScreenDto,
    MemberResultMatchDto,
    MemberResultsScreenDto,
    ResultsSummaryDto,
    SyncLogDto,
)
from app.core.config import get_settings
from app.models.schema import (
    CompetitionPhase,
    CompetitionPrediction,
    CompetitionWindow,
    Match,
    MatchPrediction,
    PredictionType,
    SyncLog,
    User,
)
from app.repositories.queries import get_active_competition_window


class FrontendContractService:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def build_member_results(self, *, user: User) -> MemberResultsScreenDto:
        predictions = list(
            self.db_session.scalars(
                select(MatchPrediction)
                .where(MatchPrediction.user_id == user.id)
                .order_by(MatchPrediction.created_at.asc(), MatchPrediction.id.asc())
            ).all()
        )
        by_match_id = {prediction.match_id: prediction for prediction in predictions}
        matches: list[Match] = []
        if by_match_id:
            matches = list(
                self.db_session.scalars(
                    select(Match)
                    .where(Match.id.in_(tuple(by_match_id)))
                    .order_by(Match.starts_at.asc(), Match.id.asc())
                ).all()
            )
        champion_points = self._competition_points(user.id, PredictionType.CHAMPION)
        top_scorer_points = self._competition_points(user.id, PredictionType.TOP_SCORER)
        rows: list[MemberResultMatchDto] = []
        exact_hits = 0
        correct_outcomes = 0
        brazil_bonus_hits = 0
        total_points = champion_points + top_scorer_points
        for match in matches:
            prediction = by_match_id[match.id]
            points_awarded = prediction.points_awarded or 0
            total_points += points_awarded
            is_exact = (
                match.official_home_goals is not None
                and match.official_away_goals is not None
                and prediction.home_goals == match.official_home_goals
                and prediction.away_goals == match.official_away_goals
            )
            same_outcome = False
            if (
                match.official_home_goals is not None
                and match.official_away_goals is not None
                and not is_exact
            ):
                same_outcome = self._resolve_outcome(prediction.home_goals, prediction.away_goals) == self._resolve_outcome(
                    match.official_home_goals,
                    match.official_away_goals,
                )
            if is_exact:
                exact_hits += 1
            elif same_outcome:
                correct_outcomes += 1
            if match.involves_brazil and points_awarded > 0:
                brazil_bonus_hits += 1
            rows.append(
                MemberResultMatchDto(
                    matchId=match.id,
                    phase=match.phase.value,
                    slot=match.bracket_slot,
                    groupName=match.group_name,
                    status=match.status,
                    startsAt=match.starts_at,
                    homeTeam=match.home_team_name,
                    awayTeam=match.away_team_name,
                    officialHomeGoals=match.official_home_goals,
                    officialAwayGoals=match.official_away_goals,
                    predictedHomeGoals=prediction.home_goals,
                    predictedAwayGoals=prediction.away_goals,
                    pointsAwarded=prediction.points_awarded,
                    involvesBrazil=match.involves_brazil,
                )
            )
        return MemberResultsScreenDto(
            summary=ResultsSummaryDto(
                totalPoints=total_points,
                exactHits=exact_hits,
                correctOutcomes=correct_outcomes,
                brazilBonusHits=brazil_bonus_hits,
                championPoints=champion_points,
                topScorerPoints=top_scorer_points,
            ),
            matches=rows,
        )

    def build_member_bracket(self, *, user: User) -> MemberBracketScreenDto:
        champion_prediction = self.db_session.scalar(
            select(CompetitionPrediction.selection_label).where(
                CompetitionPrediction.user_id == user.id,
                CompetitionPrediction.prediction_type == PredictionType.CHAMPION,
            )
        )
        knockout_matches: list[Match] = list(
            self.db_session.scalars(
                select(Match)
                .where(Match.phase != CompetitionPhase.GROUP_STAGE)
                .order_by(Match.bracket_slot.asc(), Match.starts_at.asc(), Match.id.asc())
            ).all()
        )
        seed_matches = self._load_knockout_seed_matches() if not knockout_matches else []
        rows = [
            BracketMatchDto(
                matchId=getattr(match, "id", None),
                phase=match.phase.value if isinstance(match, Match) else str(match["phase"]),
                slot=(match.bracket_slot or "TBD") if isinstance(match, Match) else str(match["slot"]),
                startsAt=match.starts_at if isinstance(match, Match) else self._coerce_datetime(match.get("startsAt")),
                homeTeam=match.home_team_name if isinstance(match, Match) else self._coerce_string(match.get("homeTeam")),
                awayTeam=match.away_team_name if isinstance(match, Match) else self._coerce_string(match.get("awayTeam")),
                winnerTeam=match.winner_team_name if isinstance(match, Match) else None,
                feederHomeKey=match.feeder_home_key if isinstance(match, Match) else self._coerce_string(match.get("feederHomeKey")),
                feederAwayKey=match.feeder_away_key if isinstance(match, Match) else self._coerce_string(match.get("feederAwayKey")),
                hasManualOverride=match.has_manual_override if isinstance(match, Match) else False,
            )
            for match in (knockout_matches if knockout_matches else seed_matches)
        ]
        third_place_slots = [
            BracketThirdPlaceSlotDto(
                slot=slot,
                assignedGroup=None,
                assignedTeam=next((row.awayTeam for row in rows if row.slot == slot), None),
            )
            for slot in ("M74", "M77", "M79", "M80", "M81", "M82", "M85", "M87")
        ]
        return MemberBracketScreenDto(
            championPrediction=champion_prediction,
            thirdPlaceSlots=third_place_slots,
            matches=rows,
        )

    def build_admin_dashboard(self) -> AdminDashboardScreenDto:
        users = list(self.db_session.scalars(select(User)).all())
        matches = list(self.db_session.scalars(select(Match)).all())
        latest_syncs = list(
            self.db_session.scalars(
                select(SyncLog).order_by(SyncLog.created_at.desc(), SyncLog.id.desc()).limit(5)
            ).all()
        )
        competition_window = get_active_competition_window(self.db_session)
        return AdminDashboardScreenDto(
            users=AdminUserCountsDto(
                total=len(users),
                approved=sum(1 for user in users if user.access_status.value == "APPROVED"),
                pending=sum(1 for user in users if user.access_status.value == "PENDING"),
                rejected=sum(1 for user in users if user.access_status.value == "REJECTED"),
                blocked=sum(1 for user in users if user.access_status.value == "BLOCKED"),
            ),
            matches=self._match_status_counts(matches),
            latestSyncs=[self._sync_log_to_dto(log) for log in latest_syncs],
            predictionCloseAt=competition_window.prediction_close_at,
            exploreReleaseAt=competition_window.explore_release_at,
        )

    def build_admin_integration(self) -> AdminIntegrationScreenDto:
        settings = get_settings()
        last_syncs = list(
            self.db_session.scalars(
                select(SyncLog).order_by(SyncLog.created_at.desc(), SyncLog.id.desc()).limit(8)
            ).all()
        )
        return AdminIntegrationScreenDto(
            primaryProvider="API_FOOTBALL",
            fallbackProvider="GOOGLE_SHEETS",
            apiConfigured=settings.api_football_key is not None,
            dailyRunLimit=settings.sync.max_runs_per_day,
            allowedTerminalStatuses=list(settings.sync.allowed_terminal_statuses),
            lastSyncs=[self._sync_log_to_dto(log) for log in last_syncs],
        )

    def build_admin_matches(self) -> AdminMatchesScreenDto:
        matches = list(
            self.db_session.scalars(
                select(Match).order_by(Match.starts_at.asc(), Match.phase.asc(), Match.id.asc())
            ).all()
        )
        return AdminMatchesScreenDto(
            summary=self._match_status_counts(matches),
            matches=[self._admin_match_to_dto(match) for match in matches],
        )

    def build_admin_results(self) -> AdminMatchesScreenDto:
        matches = list(
            self.db_session.scalars(
                select(Match)
                .where(Match.official_home_goals.is_not(None), Match.official_away_goals.is_not(None))
                .order_by(Match.starts_at.desc(), Match.id.desc())
            ).all()
        )
        return AdminMatchesScreenDto(
            summary=self._match_status_counts(matches),
            matches=[self._admin_match_to_dto(match) for match in matches],
        )

    def build_admin_players(self) -> AdminPlayersScreenDto:
        settings = get_settings()
        predictions = list(
            self.db_session.scalars(
                select(CompetitionPrediction)
                .where(CompetitionPrediction.prediction_type == PredictionType.TOP_SCORER)
                .order_by(CompetitionPrediction.selection_label.asc())
            ).all()
        )
        counts = Counter((prediction.selection_key, prediction.selection_label) for prediction in predictions)
        points: Counter[tuple[str, str]] = Counter()
        for prediction in predictions:
            points[(prediction.selection_key, prediction.selection_label)] += prediction.points_awarded or 0
        leaders = [
            AdminPlayerRowDto(
                selectionKey=selection_key,
                selectionLabel=selection_label,
                predictionCount=count,
                pointsAwardedTotal=points[(selection_key, selection_label)],
            )
            for (selection_key, selection_label), count in counts.most_common(12)
        ]
        return AdminPlayersScreenDto(
            topScorerPoints=settings.scoring.top_scorer_points,
            leaders=leaders,
        )

    def build_admin_settings(self) -> AdminSettingsScreenDto:
        settings = get_settings()
        competition_window = self.db_session.scalar(
            select(CompetitionWindow)
            .where(CompetitionWindow.is_active.is_(True))
            .order_by(CompetitionWindow.updated_at.desc())
        )
        active_window = get_active_competition_window(self.db_session)
        return AdminSettingsScreenDto(
            competitionWindow={
                "id": str(competition_window.id) if competition_window is not None else "default",
                "name": competition_window.name if competition_window is not None else "default",
                "prediction_close_at": active_window.prediction_close_at.isoformat(),
                "explore_release_at": active_window.explore_release_at.isoformat(),
                "is_active": True,
            },
            scoring={
                "exact_points": settings.scoring.exact_points,
                "result_points": settings.scoring.result_points,
                "brazil_multiplier": settings.scoring.brazil_multiplier,
                "champion_points": settings.scoring.champion_points,
                "top_scorer_points": settings.scoring.top_scorer_points,
            },
            sync={
                "post_match_offset_minutes": settings.sync.post_match_offset_minutes,
                "allowed_terminal_statuses": list(settings.sync.allowed_terminal_statuses),
                "max_runs_per_day": settings.sync.max_runs_per_day,
            },
        )

    def _competition_points(self, user_id: object, prediction_type: PredictionType) -> int:
        prediction = self.db_session.scalar(
            select(CompetitionPrediction).where(
                CompetitionPrediction.user_id == user_id,
                CompetitionPrediction.prediction_type == prediction_type,
            )
        )
        return prediction.points_awarded or 0 if prediction is not None else 0

    def _match_status_counts(self, matches: list[Match]) -> MatchStatusCountsDto:
        return MatchStatusCountsDto(
            total=len(matches),
            scheduled=sum(1 for match in matches if match.status not in {"FT", "AET", "PEN"}),
            finished=sum(1 for match in matches if match.status in {"FT", "AET", "PEN"}),
            overridden=sum(1 for match in matches if match.has_manual_override),
        )

    def _sync_log_to_dto(self, log: SyncLog) -> SyncLogDto:
        return SyncLogDto(
            id=log.id,
            provider=log.provider.value,
            status=log.status.value,
            operation=log.operation,
            message=log.message or "",
            createdAt=log.created_at,
        )

    def _admin_match_to_dto(self, match: Match) -> AdminMatchRowDto:
        return AdminMatchRowDto(
            id=match.id,
            phase=match.phase.value,
            groupName=match.group_name,
            bracketSlot=match.bracket_slot,
            status=match.status,
            startsAt=match.starts_at,
            venue=match.venue,
            homeTeam=match.home_team_name,
            awayTeam=match.away_team_name,
            officialHomeGoals=match.official_home_goals,
            officialAwayGoals=match.official_away_goals,
            winnerTeam=match.winner_team_name,
            hasManualOverride=match.has_manual_override,
            externalProvider=match.external_provider.value if match.external_provider is not None else None,
            externalId=match.external_id,
        )

    def _load_knockout_seed_matches(self) -> list[dict[str, object]]:
        seed_path = Path(__file__).resolve().parents[3] / "data" / "bracket-knockout.json"
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
        rows: list[dict[str, object]] = []
        sections = ("roundOf32", "roundOf16", "quarterFinals", "semiFinals", "thirdPlace", "final")
        for section in sections:
            for row in payload.get(section, []):
                rows.append(
                    {
                        "phase": row["phase"],
                        "slot": row["slot"],
                        "startsAt": self._parse_optional_datetime(row.get("startsAt")),
                        "homeTeam": row.get("homeTeam"),
                        "awayTeam": row.get("awayTeam"),
                        "feederHomeKey": self._slot_to_feeder_key(row.get("homeSlot")),
                        "feederAwayKey": self._slot_to_feeder_key(row.get("awaySlot")),
                    }
                )
        return rows

    def _parse_optional_datetime(self, value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _slot_to_feeder_key(self, slot_payload: object) -> str | None:
        if not isinstance(slot_payload, dict):
            return None
        slot_type = slot_payload.get("type")
        group_name = slot_payload.get("group")
        if isinstance(slot_type, str) and isinstance(group_name, str):
            return f"{slot_type}:{group_name}"
        return None

    def _coerce_datetime(self, value: object) -> datetime | None:
        return value if isinstance(value, datetime) else None

    def _coerce_string(self, value: object) -> str | None:
        return value if isinstance(value, str) else None

    def _resolve_outcome(self, home_goals: int, away_goals: int) -> str:
        if home_goals > away_goals:
            return "HOME"
        if home_goals < away_goals:
            return "AWAY"
        return "DRAW"
