"""Time as a dependency, so every rule that depends on "today" can be tested."""

from datetime import UTC, date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo


class Clock(Protocol):
    def now(self) -> datetime: ...

    def today(self) -> date: ...


class SystemClock:
    """The real clock. "Today" is the user's calendar day, not UTC's."""

    def __init__(self, timezone: ZoneInfo) -> None:
        self._timezone = timezone

    def now(self) -> datetime:
        return datetime.now(UTC)

    def today(self) -> date:
        return datetime.now(self._timezone).date()


class FixedClock:
    """A clock that never moves. Used by tests and by the demo seed."""

    def __init__(self, instant: datetime, timezone: ZoneInfo) -> None:
        self._instant = instant
        self._timezone = timezone

    def now(self) -> datetime:
        return self._instant

    def today(self) -> date:
        return self._instant.astimezone(self._timezone).date()
