"""Injectable clock so date-dependent logic (reviews, streaks) is testable."""

from datetime import UTC, date, datetime, time, timedelta
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

    def day_bounds(self, day: date) -> tuple[datetime, datetime]:
        """UTC start (inclusive) and end (exclusive) of a local calendar day."""
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

    def day_bounds(self, day: date) -> tuple[datetime, datetime]:
        start = datetime.combine(day, time.min, tzinfo=self._zone)
        end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=self._zone)
        return start.astimezone(UTC), end.astimezone(UTC)
