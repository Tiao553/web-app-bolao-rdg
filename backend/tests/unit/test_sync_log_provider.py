from __future__ import annotations

from types import SimpleNamespace

from app.models.schema import SyncProvider
from app.services.sync_service import resolve_sync_log_provider


class FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar(self) -> object:
        return self._value


class FakeSession:
    def __init__(self, enum_supported: bool) -> None:
        self.bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
        self._enum_supported = enum_supported

    def execute(self, *_: object, **__: object) -> FakeResult:
        return FakeResult(self._enum_supported)


def test_resolve_sync_log_provider_falls_back_when_enum_is_missing() -> None:
    session = FakeSession(enum_supported=False)

    assert resolve_sync_log_provider(session, SyncProvider.THE_SPORTS_DB) is SyncProvider.ADMIN


def test_resolve_sync_log_provider_keeps_supported_provider() -> None:
    session = FakeSession(enum_supported=True)

    assert resolve_sync_log_provider(session, SyncProvider.THE_SPORTS_DB) is SyncProvider.THE_SPORTS_DB

