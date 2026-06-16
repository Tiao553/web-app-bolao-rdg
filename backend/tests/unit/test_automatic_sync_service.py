from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.schema import (
    Base,
    IntegrationSettings,
    SyncLog,
    SyncProvider,
    SyncStatus,
)
from app.services.automatic_sync import run_automatic_sync
from app.services.recalculation_service import (
    RecalculationStageSummary,
    RecalculationSummary,
)
from app.services.sync_service import SyncRunResult


def make_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    return factory()


def fake_recalculation_summary() -> RecalculationSummary:
    stage = RecalculationStageSummary(status="ok", updated_count=0, skipped_count=0, notes=None)
    return RecalculationSummary(
        executed_at=datetime.now(timezone.utc),
        standings=stage,
        bracket=stage,
        match_points=stage,
        competition_points=stage,
        ranking=stage,
        ranking_rows=[],
    )


class FakeSyncService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def run_scheduled_sync(self, db_session: Session, **kwargs) -> SyncRunResult:
        self.calls.append({"db_session": db_session, **kwargs})
        now = datetime.now(timezone.utc)
        return SyncRunResult(
            provider=SyncProvider.THE_SPORTS_DB,
            started_at=now,
            finished_at=now,
            outcomes=(),
            used_fallback=False,
        )


def test_run_automatic_sync_recalculates_and_records_summary(monkeypatch) -> None:
    db_session = make_session()
    db_session.add(IntegrationSettings(auto_sync_enabled=True, auto_sync_interval_minutes=1))
    db_session.commit()

    fake_service = FakeSyncService()
    recalculation = fake_recalculation_summary()
    calls: list[Session] = []

    def fake_recalculate(db_session: Session) -> RecalculationSummary:
        calls.append(db_session)
        return recalculation

    monkeypatch.setattr(
        "app.services.automatic_sync.recalculate_competition_state",
        fake_recalculate,
    )

    result = run_automatic_sync(
        db_session,
        sync_service=fake_service,
        now_provider=lambda: datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc),
        trigger_source="external_trigger",
    )

    assert result.status is SyncStatus.SUCCESS
    assert result.recalculation == recalculation
    assert len(fake_service.calls) == 1
    service_call = fake_service.calls[0]
    assert service_call["db_session"] is db_session
    assert service_call["requested_provider"] is SyncProvider.THE_SPORTS_DB
    assert service_call["allow_google_sheets_fallback"] is False
    assert service_call["include_top_scorers"] is False
    assert service_call["respect_timing_window"] is False
    assert callable(service_call["recalculation_hook"])
    assert calls == [db_session]

    summary_log = db_session.scalar(
        select(SyncLog)
        .where(SyncLog.operation == "automatic_sync")
        .order_by(SyncLog.created_at.desc(), SyncLog.id.desc())
    )
    assert summary_log is not None
    assert summary_log.status is SyncStatus.SUCCESS
    assert summary_log.result_code == "automatic_sync_completed"
    assert summary_log.payload["trigger_source"] == "external_trigger"

