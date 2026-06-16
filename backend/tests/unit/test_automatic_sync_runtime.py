from __future__ import annotations

import asyncio

import pytest

from app.models.schema import SyncProvider, SyncStatus
from app.services.automatic_sync import AutomaticSyncExecution, AutoSyncWorker


class FakeSession:
    def __init__(self) -> None:
        self.commit_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def close(self) -> None:
        self.close_calls += 1


def test_auto_sync_worker_run_once_commits_session(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()

    def fake_run_automatic_sync(db_session: FakeSession, *, trigger_source: str) -> AutomaticSyncExecution:
        assert db_session is session
        assert trigger_source == "runtime_worker"
        return AutomaticSyncExecution(
            provider=SyncProvider.THE_SPORTS_DB,
            status=SyncStatus.SUCCESS,
            operation="automatic_sync",
            message="ok",
            recalculation=None,
        )

    monkeypatch.setattr(
        "app.services.automatic_sync.run_automatic_sync",
        fake_run_automatic_sync,
    )

    worker = AutoSyncWorker(
        session_factory=lambda: session,
        poll_seconds=60,
    )
    asyncio.run(worker.run_once())

    assert session.commit_calls == 1
    assert session.rollback_calls == 0
    assert session.close_calls == 1


def test_auto_sync_worker_run_once_rolls_back_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()

    def fake_run_automatic_sync(db_session: FakeSession, *, trigger_source: str) -> AutomaticSyncExecution:
        assert db_session is session
        assert trigger_source == "runtime_worker"
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.services.automatic_sync.run_automatic_sync",
        fake_run_automatic_sync,
    )

    worker = AutoSyncWorker(
        session_factory=lambda: session,
        poll_seconds=60,
    )

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(worker.run_once())

    assert session.commit_calls == 0
    assert session.rollback_calls == 1
    assert session.close_calls == 1
