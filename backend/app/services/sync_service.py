from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.api_football import (
    APIFootballClient,
    ProviderConfigurationError,
    ProviderError,
    ProviderMatchRecord,
    ProviderResponseError,
    ProviderSyncBatch,
    ProviderTopScorer,
)
from app.integrations.google_sheets import GoogleSheetsClient
from app.integrations.the_sports_db import TheSportsDBClient
from app.models.schema import Match, SyncLog, SyncProvider, SyncStatus


@dataclass(frozen=True, slots=True)
class MatchEligibility:
    eligible: bool
    result_code: str
    message: str


@dataclass(frozen=True, slots=True)
class MatchSyncOutcome:
    provider: SyncProvider
    status: SyncStatus
    result_code: str
    message: str
    match_id: UUID | None
    external_id: str | None
    changed_fields: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SyncRecalculationRequest:
    provider: SyncProvider
    run_at: datetime
    changed_match_ids: tuple[UUID, ...]
    changed_external_ids: tuple[str, ...]
    top_scorers: tuple[ProviderTopScorer, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SyncRunResult:
    provider: SyncProvider
    started_at: datetime
    finished_at: datetime
    outcomes: tuple[MatchSyncOutcome, ...]
    used_fallback: bool = False

    @property
    def success_count(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.status is SyncStatus.SUCCESS)

    @property
    def skipped_count(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.status is SyncStatus.SKIPPED)

    @property
    def failure_count(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.status is SyncStatus.FAILURE)


class RecalculationHook(Protocol):
    def __call__(self, db_session: Session, request: SyncRecalculationRequest) -> None: ...


class SyncService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        the_sports_db_client: TheSportsDBClient | None = None,
        api_football_client: APIFootballClient | None = None,
        google_sheets_client: GoogleSheetsClient | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        api_key = self._settings.api_football_key.get_secret_value() if self._settings.api_football_key is not None else None
        self._the_sports_db_client = the_sports_db_client or TheSportsDBClient()
        self._api_football_client = api_football_client or APIFootballClient(api_key=api_key)
        self._google_sheets_client = google_sheets_client or GoogleSheetsClient()
        self._now_provider = now_provider or self._default_now

    def run_scheduled_sync(
        self,
        db_session: Session,
        *,
        created_by_user_id: UUID | None = None,
        requested_provider: SyncProvider | None = None,
        allow_google_sheets_fallback: bool = False,
        fixture_ids: Sequence[str] | None = None,
        include_top_scorers: bool = True,
        recalculation_hook: RecalculationHook | None = None,
        respect_timing_window: bool = True,
    ) -> SyncRunResult:
        started_at = self._now_provider()
        provider_batch, used_fallback = self._fetch_provider_batch(
            requested_provider=requested_provider,
            allow_google_sheets_fallback=allow_google_sheets_fallback,
            fixture_ids=fixture_ids,
            include_top_scorers=include_top_scorers,
        )
        matches = self._load_matches(db_session)
        target_matches = self._filter_target_matches(
            matches=matches,
            now=started_at,
            fixture_ids=fixture_ids,
            respect_timing_window=respect_timing_window,
        )
        outcomes: list[MatchSyncOutcome] = []
        changed_match_ids: list[UUID] = []
        changed_external_ids: list[str] = []
        for provider_match in provider_batch.matches:
            local_match = self._match_local_record(matches=target_matches, provider_match=provider_match)
            if local_match is None:
                if fixture_ids is not None:
                    outcomes.append(
                        self._record_outcome(
                            db_session,
                            provider=provider_batch.provider,
                            status=SyncStatus.SKIPPED,
                            result_code="missing_local_match",
                            message="No local match could be matched to the provider payload",
                            match=None,
                            created_by_user_id=created_by_user_id,
                            payload=self._build_log_payload(provider_match=provider_match),
                        )
                    )
                continue
            eligibility = self._evaluate_eligibility(
                local_match=local_match,
                provider_match=provider_match,
                now=started_at,
                respect_timing_window=respect_timing_window,
            )
            if not eligibility.eligible:
                if fixture_ids is None and eligibility.result_code in {"not_due_yet", "non_terminal_status"}:
                    continue
                outcomes.append(
                    self._record_outcome(
                        db_session,
                        provider=provider_batch.provider,
                        status=SyncStatus.SKIPPED,
                        result_code=eligibility.result_code,
                        message=eligibility.message,
                        match=local_match,
                        created_by_user_id=created_by_user_id,
                        payload=self._build_log_payload(provider_match=provider_match),
                    )
                )
                continue
            outcome = self._merge_provider_match(
                db_session=db_session,
                local_match=local_match,
                provider_match=provider_match,
                fetched_at=provider_batch.fetched_at,
                created_by_user_id=created_by_user_id,
            )
            outcomes.append(outcome)
            if outcome.status is SyncStatus.SUCCESS and outcome.changed_fields:
                changed_match_ids.append(local_match.id)
                changed_external_ids.append(provider_match.external_id)
        if recalculation_hook is not None and (changed_match_ids or provider_batch.top_scorers):
            db_session.flush()
            recalculation_hook(
                db_session,
                SyncRecalculationRequest(
                    provider=provider_batch.provider,
                    run_at=self._now_provider(),
                    changed_match_ids=tuple(changed_match_ids),
                    changed_external_ids=tuple(changed_external_ids),
                    top_scorers=provider_batch.top_scorers,
                    metadata=dict(provider_batch.metadata),
                ),
            )
        return SyncRunResult(
            provider=provider_batch.provider,
            started_at=started_at,
            finished_at=self._now_provider(),
            outcomes=tuple(outcomes),
            used_fallback=used_fallback,
        )

    def run_manual_match_sync(
        self,
        db_session: Session,
        *,
        fixture_id: str,
        created_by_user_id: UUID | None = None,
        requested_provider: SyncProvider | None = None,
        allow_google_sheets_fallback: bool = False,
        include_top_scorers: bool = True,
        recalculation_hook: RecalculationHook | None = None,
    ) -> SyncRunResult:
        return self.run_scheduled_sync(
            db_session,
            created_by_user_id=created_by_user_id,
            requested_provider=requested_provider,
            allow_google_sheets_fallback=allow_google_sheets_fallback,
            fixture_ids=(fixture_id,),
            include_top_scorers=include_top_scorers,
            recalculation_hook=recalculation_hook,
            respect_timing_window=False,
        )

    def _fetch_provider_batch(
        self,
        *,
        requested_provider: SyncProvider | None,
        allow_google_sheets_fallback: bool,
        fixture_ids: Sequence[str] | None,
        include_top_scorers: bool,
    ) -> tuple[ProviderSyncBatch, bool]:
        if requested_provider is SyncProvider.THE_SPORTS_DB:
            return self._the_sports_db_client.fetch_match_batch(
                fixture_ids=fixture_ids,
                include_top_scorers=include_top_scorers,
            ), False
        if requested_provider is SyncProvider.GOOGLE_SHEETS:
            return self._google_sheets_client.fetch_match_batch(fixture_ids=fixture_ids, include_top_scorers=include_top_scorers), False
        if requested_provider is SyncProvider.API_FOOTBALL:
            return self._api_football_client.fetch_match_batch(fixture_ids=fixture_ids, include_top_scorers=include_top_scorers), False
        try:
            return self._the_sports_db_client.fetch_match_batch(
                fixture_ids=fixture_ids,
                include_top_scorers=include_top_scorers,
            ), False
        except (ProviderConfigurationError, ProviderResponseError, ProviderError):
            try:
                return self._api_football_client.fetch_match_batch(
                    fixture_ids=fixture_ids,
                    include_top_scorers=include_top_scorers,
                ), True
            except (ProviderConfigurationError, ProviderResponseError, ProviderError):
                if not allow_google_sheets_fallback:
                    raise
            return self._google_sheets_client.fetch_match_batch(fixture_ids=fixture_ids, include_top_scorers=include_top_scorers), True

    def _load_matches(self, db_session: Session) -> tuple[Match, ...]:
        return tuple(db_session.scalars(select(Match).order_by(Match.starts_at.asc(), Match.id.asc())).all())

    def _filter_target_matches(
        self,
        *,
        matches: Sequence[Match],
        now: datetime,
        fixture_ids: Sequence[str] | None,
        respect_timing_window: bool,
    ) -> tuple[Match, ...]:
        if fixture_ids is not None or not respect_timing_window:
            return tuple(matches)
        threshold = now - timedelta(minutes=self._settings.sync.post_match_offset_minutes)
        return tuple(match for match in matches if self._as_utc(match.starts_at) <= threshold)

    def _match_local_record(self, *, matches: Sequence[Match], provider_match: ProviderMatchRecord) -> Match | None:
        for match in matches:
            if match.external_provider is provider_match.provider and match.external_id == provider_match.external_id:
                return match
        for match in matches:
            if match.external_id == provider_match.external_id:
                return match
        if provider_match.bracket_slot is not None:
            for match in matches:
                if match.bracket_slot == provider_match.bracket_slot:
                    return match
        identity = self._identity_key(
            home_team_name=provider_match.home_team_name,
            away_team_name=provider_match.away_team_name,
            starts_at=provider_match.starts_at,
        )
        for match in matches:
            if self._identity_key(
                home_team_name=match.home_team_name,
                away_team_name=match.away_team_name,
                starts_at=self._as_utc(match.starts_at),
            ) == identity:
                return match
        return None

    def _evaluate_eligibility(
        self,
        *,
        local_match: Match,
        provider_match: ProviderMatchRecord,
        now: datetime,
        respect_timing_window: bool,
    ) -> MatchEligibility:
        allowed_statuses = set(self._settings.sync.allowed_terminal_statuses)
        if respect_timing_window:
            threshold = provider_match.starts_at + timedelta(minutes=self._settings.sync.post_match_offset_minutes)
            if threshold > now:
                return MatchEligibility(False, "not_due_yet", "Match is not yet eligible for post-match sync")
        if provider_match.status not in allowed_statuses:
            return MatchEligibility(False, "non_terminal_status", "Provider payload is not in a terminal status")
        if local_match.has_manual_override and not self._has_material_difference(local_match=local_match, provider_match=provider_match):
            return MatchEligibility(True, "noop", "Provider payload matches local overridden record")
        return MatchEligibility(True, "eligible", "Match is eligible for sync")

    def _merge_provider_match(
        self,
        *,
        db_session: Session,
        local_match: Match,
        provider_match: ProviderMatchRecord,
        fetched_at: datetime,
        created_by_user_id: UUID | None,
    ) -> MatchSyncOutcome:
        if local_match.has_manual_override:
            return self._record_outcome(
                db_session,
                provider=provider_match.provider,
                status=SyncStatus.SKIPPED,
                result_code="skipped_manual_override",
                message="Local record has manual override and was preserved",
                match=local_match,
                created_by_user_id=created_by_user_id,
                payload=self._build_log_payload(provider_match=provider_match),
            )
        changed_fields: list[str] = []
        for field_name, new_value in (
            ("external_provider", provider_match.provider),
            ("external_id", provider_match.external_id),
            ("phase", provider_match.phase),
            ("stage_round", provider_match.stage_round),
            ("group_name", provider_match.group_name),
            ("bracket_slot", provider_match.bracket_slot),
            ("starts_at", provider_match.starts_at),
            ("venue", provider_match.venue),
            ("home_team_name", provider_match.home_team_name),
            ("away_team_name", provider_match.away_team_name),
            ("home_team_fifa_code", provider_match.home_team_fifa_code),
            ("away_team_fifa_code", provider_match.away_team_fifa_code),
            ("involves_brazil", provider_match.involves_brazil),
            ("status", provider_match.status),
            ("official_home_goals", provider_match.official_home_goals),
            ("official_away_goals", provider_match.official_away_goals),
            ("winner_team_name", provider_match.winner_team_name),
        ):
            self._apply_if_changed(local_match, field_name, new_value, changed_fields)
        local_match.source_payload = dict(provider_match.source_payload)
        local_match.synced_at = fetched_at
        return self._record_outcome(
            db_session,
            provider=provider_match.provider,
            status=SyncStatus.SUCCESS,
            result_code="updated" if changed_fields else "noop",
            message="Local match merged with provider payload" if changed_fields else "Provider payload produced no material changes",
            match=local_match,
            created_by_user_id=created_by_user_id,
            payload=self._build_log_payload(provider_match=provider_match, changed_fields=tuple(changed_fields)),
            changed_fields=tuple(changed_fields),
        )

    def _record_outcome(
        self,
        db_session: Session,
        *,
        provider: SyncProvider,
        status: SyncStatus,
        result_code: str,
        message: str,
        match: Match | None,
        created_by_user_id: UUID | None,
        payload: dict[str, Any],
        changed_fields: tuple[str, ...] = (),
    ) -> MatchSyncOutcome:
        db_session.add(
            SyncLog(
                provider=resolve_sync_log_provider(db_session, provider),
                status=status,
                operation="match_sync",
                match_id=match.id if match is not None else None,
                created_by_user_id=created_by_user_id,
                result_code=result_code,
                message=message,
                payload=payload,
            )
        )
        return MatchSyncOutcome(
            provider=provider,
            status=status,
            result_code=result_code,
            message=message,
            match_id=match.id if match is not None else None,
            external_id=match.external_id if match is not None else payload.get("external_id"),
            changed_fields=changed_fields,
            payload=payload,
        )

    def _build_log_payload(self, *, provider_match: ProviderMatchRecord, changed_fields: tuple[str, ...] = ()) -> dict[str, Any]:
        return {
            "external_id": provider_match.external_id,
            "status": provider_match.status,
            "phase": provider_match.phase.value,
            "group_name": provider_match.group_name,
            "bracket_slot": provider_match.bracket_slot,
            "changed_fields": list(changed_fields),
            "provider_payload": dict(provider_match.source_payload),
        }

    def _has_material_difference(self, *, local_match: Match, provider_match: ProviderMatchRecord) -> bool:
        return any((
            local_match.phase != provider_match.phase,
            local_match.stage_round != provider_match.stage_round,
            local_match.group_name != provider_match.group_name,
            local_match.bracket_slot != provider_match.bracket_slot,
            self._as_utc(local_match.starts_at) != provider_match.starts_at,
            local_match.venue != provider_match.venue,
            local_match.home_team_name != provider_match.home_team_name,
            local_match.away_team_name != provider_match.away_team_name,
            local_match.home_team_fifa_code != provider_match.home_team_fifa_code,
            local_match.away_team_fifa_code != provider_match.away_team_fifa_code,
            local_match.involves_brazil != provider_match.involves_brazil,
            local_match.status != provider_match.status,
            local_match.official_home_goals != provider_match.official_home_goals,
            local_match.official_away_goals != provider_match.official_away_goals,
            local_match.winner_team_name != provider_match.winner_team_name,
        ))

    def _apply_if_changed(self, match: Match, field_name: str, new_value: Any, changed_fields: list[str]) -> None:
        current_value = getattr(match, field_name)
        if field_name == "starts_at":
            current_value = self._as_utc(current_value)
        if current_value == new_value:
            return
        setattr(match, field_name, new_value)
        changed_fields.append(field_name)

    def _identity_key(self, *, home_team_name: str, away_team_name: str, starts_at: datetime) -> tuple[str, str, datetime]:
        normalized_starts_at = starts_at.astimezone(timezone.utc).replace(second=0, microsecond=0)
        return (home_team_name.strip().casefold(), away_team_name.strip().casefold(), normalized_starts_at)

    def _as_utc(self, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    def _default_now(self) -> datetime:
        return datetime.now(timezone.utc)


def resolve_sync_log_provider(db_session: Session, provider: SyncProvider) -> SyncProvider:
    if provider is not SyncProvider.THE_SPORTS_DB:
        return provider
    bind = db_session.bind
    if bind is None or bind.dialect.name != "postgresql":
        return provider
    try:
        supported = bool(
            db_session.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_enum e
                        JOIN pg_type t ON t.oid = e.enumtypid
                        WHERE t.typname = 'sync_log_provider_enum'
                          AND e.enumlabel = :label
                    )
                    """
                ),
                {"label": provider.value},
            ).scalar()
        )
    except Exception:
        return SyncProvider.ADMIN
    return provider if supported else SyncProvider.ADMIN
