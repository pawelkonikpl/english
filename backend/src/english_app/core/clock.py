"""Injectable clock so date-dependent logic (reviews, streaks) is testable."""

from datetime import UTC, date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo


class Clock(Protocol):
    def now(self) -> datetime:
        """Current time, timezone-aware, in UTC."""
        ...

    def today(self) -> date:
        """Current calendar date in the learner's timezone."""
        ...

    def local_date(self, moment: datetime) -> date:
        """Calendar date of a UTC moment in the learner's timezone."""
        ...


class SystemClock:
    def __init__(self, timezone: str) -> None:
        self._zone = ZoneInfo(timezone)

    def now(self) -> datetime:
        return datetime.now(UTC)

    def today(self) -> date:
        return self.local_date(self.now())

    def local_date(self, moment: datetime) -> date:
        if moment.tzinfo is None:
            # SQLite returns naive datetimes; everything is stored in UTC.
            moment = moment.replace(tzinfo=UTC)
        return moment.astimezone(self._zone).date()
