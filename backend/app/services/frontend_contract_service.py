from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

_DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parents[2] / "data")))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.frontend import (
    AdminDashboardScreenDto,
    AdminIntegrationScreenDto,
    AdminMatchesScreenDto,
    AdminMatchRowDto,
    AdminPlayerRowDto,
    AdminPlayersScreenDto,
    AdminPhaseConfigDto,
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
    IntegrationSettings,
    Match,
    MatchPrediction,
    PredictionType,
    SyncLog,
    SyncProvider,
    User,
)
from app.repositories.queries import get_active_competition_window, get_active_scoring_rule, list_active_competition_phase_configs
from app.services.integration_settings import load_integration_settings
from app.services.match_status import is_terminal_match_status
from app.services.team_metadata import get_players_by_id, get_team_metadata


class FrontendContractService:
    AUTO_SYNC_INTERVAL_OPTIONS = [1, 5, 15, 60]

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
            home_team = get_team_metadata(match.home_team_fifa_code, match.home_team_name)
            away_team = get_team_metadata(match.away_team_fifa_code, match.away_team_name)
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
                    homeTeam=home_team.name,
                    homeCode=home_team.code,
                    homeIso2=home_team.iso2,
                    homeFlag=home_team.flag,
                    awayTeam=away_team.name,
                    awayCode=away_team.code,
                    awayIso2=away_team.iso2,
                    awayFlag=away_team.flag,
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
        standings_by_group = self._compute_group_standings()
        seed_matches = self._load_knockout_seed_matches() if not knockout_matches else []
        rows = [
            self._bracket_match_to_dto(match, standings_by_group=standings_by_group)
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

    def _compute_group_standings(self) -> dict[str, list[dict]]:
        """Returns {group: [sorted team dicts]} from finished group stage matches."""
        from collections import defaultdict
        group_matches = list(
            self.db_session.scalars(
                select(Match).where(Match.phase == CompetitionPhase.GROUP_STAGE)
            ).all()
        )
        team_data: dict[str, dict[str, dict]] = defaultdict(dict)
        for m in group_matches:
            grp = m.group_name or "?"
            for code, name in [
                (m.home_team_fifa_code or m.home_team_name, m.home_team_name),
                (m.away_team_fifa_code or m.away_team_name, m.away_team_name),
            ]:
                if code not in team_data[grp]:
                    team = get_team_metadata(code, name)
                    team_data[grp][code] = {"meta": team, "p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0}
        for m in group_matches:
            if m.official_home_goals is None or m.official_away_goals is None:
                continue
            grp = m.group_name or "?"
            hg, ag = m.official_home_goals, m.official_away_goals
            hc = m.home_team_fifa_code or m.home_team_name
            ac = m.away_team_fifa_code or m.away_team_name
            for code in (hc, ac):
                team_data[grp][code]["p"] += 1
            team_data[grp][hc]["gf"] += hg; team_data[grp][hc]["ga"] += ag
            team_data[grp][ac]["gf"] += ag; team_data[grp][ac]["ga"] += hg
            if hg > ag:
                team_data[grp][hc]["w"] += 1; team_data[grp][ac]["l"] += 1
            elif hg < ag:
                team_data[grp][ac]["w"] += 1; team_data[grp][hc]["l"] += 1
            else:
                team_data[grp][hc]["d"] += 1; team_data[grp][ac]["d"] += 1
        result: dict[str, list[dict]] = {}
        for grp, teams in team_data.items():
            sorted_teams = sorted(
                [{"meta": d["meta"], "pts": d["w"] * 3 + d["d"], "gd": d["gf"] - d["ga"], "gf": d["gf"], "p": d["p"]} for d in teams.values()],
                key=lambda x: (-x["pts"], -x["gd"], -x["gf"], x["meta"].name),
            )
            result[grp] = sorted_teams
        return result

    def build_admin_dashboard(self) -> AdminDashboardScreenDto:
        users = list(self.db_session.scalars(select(User).where(User.is_active.is_(True))).all())
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

    def build_admin_integration(
        self,
        *,
        integration_settings: IntegrationSettings | None = None,
    ) -> AdminIntegrationScreenDto:
        settings = get_settings()
        now = datetime.now(timezone.utc)
        last_syncs = list(
            self.db_session.scalars(
                select(SyncLog).order_by(SyncLog.created_at.desc(), SyncLog.id.desc()).limit(8)
            ).all()
        )
        integration_settings = integration_settings or self._get_integration_settings()
        last_auto_sync = self.db_session.scalar(
            select(SyncLog)
            .where(SyncLog.operation == "automatic_sync")
            .order_by(SyncLog.created_at.desc(), SyncLog.id.desc())
        )
        auto_sync_enabled = integration_settings.auto_sync_enabled if integration_settings is not None else False
        auto_sync_interval = integration_settings.auto_sync_interval_minutes if integration_settings is not None else 60
        last_auto_sync_at = last_auto_sync.created_at if last_auto_sync is not None else None
        next_auto_sync_at = None
        auto_sync_status = "disabled"
        if auto_sync_enabled:
            if last_auto_sync_at is None:
                auto_sync_status = "ready"
                next_auto_sync_at = now
            else:
                next_auto_sync_at = last_auto_sync_at + timedelta(minutes=auto_sync_interval)
                auto_sync_status = "ready" if next_auto_sync_at <= now else "waiting"
        return AdminIntegrationScreenDto(
            primaryProvider=SyncProvider.THE_SPORTS_DB.value,
            fallbackProvider=SyncProvider.API_FOOTBALL.value,
            activeProvider=SyncProvider.THE_SPORTS_DB.value,
            apiConfigured=True,
            dailyRunLimit=settings.sync.max_runs_per_day,
            allowedTerminalStatuses=list(settings.sync.allowed_terminal_statuses),
            autoSyncEnabled=auto_sync_enabled,
            autoSyncIntervalMinutes=auto_sync_interval,
            autoSyncIntervalOptions=list(self.AUTO_SYNC_INTERVAL_OPTIONS),
            schedulerMode="EXTERNAL_CRON",
            cronTokenConfigured=settings.sync_admin_token is not None and bool(settings.sync_admin_token.get_secret_value().strip()),
            lastAutoSyncAt=last_auto_sync_at,
            nextAutoSyncAt=next_auto_sync_at,
            autoSyncStatus=auto_sync_status,
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
        scoring_rule = get_active_scoring_rule(self.db_session)
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
        player_stats = self._load_player_stats()
        leaders = [
            self._admin_player_to_dto(selection_key, selection_label, count, points[(selection_key, selection_label)], player_stats)
            for (selection_key, selection_label), count in counts.most_common(12)
        ]
        return AdminPlayersScreenDto(
            topScorerPoints=scoring_rule.top_scorer_points,
            leaders=leaders,
        )

    def _load_player_stats(self) -> dict[str, dict[str, int]]:
        path = _DATA_DIR / "player-stats.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def build_admin_settings(self) -> AdminSettingsScreenDto:
        active_window = get_active_competition_window(self.db_session)
        phase_configs = list_active_competition_phase_configs(self.db_session)
        scoring_rule = get_active_scoring_rule(self.db_session)
        legacy_window = self.db_session.scalar(
            select(CompetitionWindow)
            .where(CompetitionWindow.is_active.is_(True))
            .order_by(CompetitionWindow.updated_at.desc())
        )
        if phase_configs:
            force_locked_phases = sum(1 << idx for idx, phase in enumerate(phase_configs) if phase.is_force_locked)
        else:
            force_locked_phases = (legacy_window.force_locked_phases or 0) if legacy_window is not None else 0
        return AdminSettingsScreenDto(
            competitionWindow={
                "id": "derived",
                "name": "phase-configs",
                "prediction_close_at": active_window.prediction_close_at.isoformat(),
                "explore_release_at": active_window.explore_release_at.isoformat(),
                "is_active": True,
            },
            phaseConfigs=[
                AdminPhaseConfigDto(
                    id=str(phase.id),
                    phaseKey=phase.phase_key,
                    label=phase.label,
                    phase=phase.phase,
                    stageRound=phase.stage_round,
                    sortOrder=phase.sort_order,
                    firstMatchStartsAt=phase.first_match_starts_at,
                    lockAt=phase.lock_at,
                    exploreAt=phase.explore_at,
                    forceLocked=phase.is_force_locked,
                    isActive=phase.is_active,
                )
                for phase in phase_configs
            ],
            forceLockedPhases=force_locked_phases,
            scoring={
                "exact_points": scoring_rule.exact_points,
                "result_points": scoring_rule.result_points,
                "brazil_multiplier": scoring_rule.brazil_multiplier,
                "champion_points": scoring_rule.champion_points,
                "top_scorer_points": scoring_rule.top_scorer_points,
            },
            sync={
                "post_match_offset_minutes": get_settings().sync.post_match_offset_minutes,
                "allowed_terminal_statuses": list(get_settings().sync.allowed_terminal_statuses),
                "max_runs_per_day": get_settings().sync.max_runs_per_day,
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

    def _get_integration_settings(self) -> IntegrationSettings | None:
        return load_integration_settings(self.db_session)

    def _match_status_counts(self, matches: list[Match]) -> MatchStatusCountsDto:
        return MatchStatusCountsDto(
            total=len(matches),
            scheduled=sum(1 for match in matches if not is_terminal_match_status(match.status)),
            finished=sum(1 for match in matches if is_terminal_match_status(match.status)),
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
        home_team = get_team_metadata(match.home_team_fifa_code, match.home_team_name)
        away_team = get_team_metadata(match.away_team_fifa_code, match.away_team_name)
        return AdminMatchRowDto(
            id=match.id,
            phase=match.phase.value,
            groupName=match.group_name,
            bracketSlot=match.bracket_slot,
            status=match.status,
            startsAt=match.starts_at,
            venue=match.venue,
            homeTeam=home_team.name,
            homeCode=home_team.code,
            homeIso2=home_team.iso2,
            homeFlag=home_team.flag,
            awayTeam=away_team.name,
            awayCode=away_team.code,
            awayIso2=away_team.iso2,
            awayFlag=away_team.flag,
            officialHomeGoals=match.official_home_goals,
            officialAwayGoals=match.official_away_goals,
            winnerTeam=match.winner_team_name,
            hasManualOverride=match.has_manual_override,
            externalProvider=match.external_provider.value if match.external_provider is not None else None,
            externalId=match.external_id,
            goalScorers=(match.source_payload or {}).get("goal_scorers", []),
        )

    def _resolve_slot_team(self, slot_key: str | None, standings: dict[str, list[dict]]) -> object:
        """Resolve WINNER:A or RUNNER_UP:B to a TeamMetadata from current standings."""
        if not slot_key or ":" not in slot_key:
            return None
        slot_type, group = slot_key.split(":", 1)
        group_table = standings.get(group, [])
        if slot_type == "WINNER" and len(group_table) >= 1:
            return group_table[0]["meta"]
        if slot_type == "RUNNER_UP" and len(group_table) >= 2:
            return group_table[1]["meta"]
        return None

    def _bracket_match_to_dto(self, match: Match | dict[str, object], standings_by_group: dict | None = None) -> BracketMatchDto:
        if isinstance(match, Match):
            home_team = get_team_metadata(match.home_team_fifa_code, match.home_team_name)
            away_team = get_team_metadata(match.away_team_fifa_code, match.away_team_name)
            home_name = None if match.home_team_name == "TBD" else home_team.name
            away_name = None if match.away_team_name == "TBD" else away_team.name
            return BracketMatchDto(
                matchId=match.id,
                phase=match.phase.value,
                slot=match.bracket_slot or "TBD",
                startsAt=match.starts_at,
                homeTeam=home_name,
                homeCode=None if home_name is None else home_team.code,
                homeIso2=None if home_name is None else home_team.iso2,
                homeFlag=None if home_name is None else home_team.flag,
                awayTeam=away_name,
                awayCode=None if away_name is None else away_team.code,
                awayIso2=None if away_name is None else away_team.iso2,
                awayFlag=None if away_name is None else away_team.flag,
                winnerTeam=match.winner_team_name,
                feederHomeKey=match.feeder_home_key,
                feederAwayKey=match.feeder_away_key,
                hasManualOverride=match.has_manual_override,
            )

        raw_home = self._coerce_string(match.get("homeTeam"))
        raw_away = self._coerce_string(match.get("awayTeam"))
        feeder_home = self._coerce_string(match.get("feederHomeKey"))
        feeder_away = self._coerce_string(match.get("feederAwayKey"))

        # Try to resolve TBD slots from current standings
        standings = standings_by_group or {}
        if raw_home in (None, "TBD") and feeder_home:
            resolved = self._resolve_slot_team(feeder_home, standings)
            if resolved:
                raw_home = resolved.code
        if raw_away in (None, "TBD") and feeder_away:
            resolved = self._resolve_slot_team(feeder_away, standings)
            if resolved:
                raw_away = resolved.code

        home_team = get_team_metadata(raw_home, raw_home)
        away_team = get_team_metadata(raw_away, raw_away)
        home_name = None if raw_home in (None, "TBD") else home_team.name
        away_name = None if raw_away in (None, "TBD") else away_team.name
        return BracketMatchDto(
            matchId=None,
            phase=str(match["phase"]),
            slot=str(match["slot"]),
            startsAt=self._coerce_datetime(match.get("startsAt")),
            homeTeam=home_name,
            homeCode=None if home_name is None else home_team.code,
            homeIso2=None if home_name is None else home_team.iso2,
            homeFlag=None if home_name is None else home_team.flag,
            awayTeam=away_name,
            awayCode=None if away_name is None else away_team.code,
            awayIso2=None if away_name is None else away_team.iso2,
            awayFlag=None if away_name is None else away_team.flag,
            winnerTeam=None,
            feederHomeKey=feeder_home,
            feederAwayKey=feeder_away,
            hasManualOverride=False,
        )

    def _admin_player_to_dto(
        self,
        selection_key: str,
        selection_label: str,
        prediction_count: int,
        points_awarded_total: int,
        player_stats: dict[str, dict[str, int]] | None = None,
    ) -> AdminPlayerRowDto:
        player = get_players_by_id().get(selection_key)
        team_code = player.get("teamCode") if isinstance(player, dict) else None
        team = get_team_metadata(team_code if isinstance(team_code, str) else None, None)
        has_team = isinstance(team_code, str) and team_code.strip() != ""
        stats = (player_stats or {}).get(selection_key, {})
        return AdminPlayerRowDto(
            selectionKey=selection_key,
            selectionLabel=selection_label,
            teamCode=team.code if has_team else None,
            teamName=team.name if has_team else None,
            teamIso2=team.iso2 if has_team else None,
            teamFlag=team.flag if has_team else None,
            predictionCount=prediction_count,
            pointsAwardedTotal=points_awarded_total,
            goals=stats.get("goals", 0),
            assists=stats.get("assists", 0),
        )

    def _load_knockout_seed_matches(self) -> list[dict[str, object]]:
        seed_path = _DATA_DIR / "bracket-knockout.json"
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
