from __future__ import annotations

TERMINAL_MATCH_STATUSES = {"FT", "AET", "PEN", "FINISHED"}


def is_terminal_match_status(status: str | None) -> bool:
    return status in TERMINAL_MATCH_STATUSES if status is not None else False

