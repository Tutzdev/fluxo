"""A calendar month as a value, so no service ever does date arithmetic by hand."""

import calendar
import re
from dataclasses import dataclass
from datetime import date
from typing import Self

_MONTH_FORMAT = re.compile(r"^(\d{4})-(\d{2})$")


@dataclass(frozen=True, slots=True, order=True)
class Month:
    year: int
    month: int

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError(f"Month must be 1-12, got {self.month}")

    @classmethod
    def parse(cls, text: str) -> Self:
        """'2026-11' -> Month(2026, 11)."""
        match = _MONTH_FORMAT.match(text)

        if match is None:
            raise ValueError(f"Expected YYYY-MM, got {text!r}")

        return cls(int(match[1]), int(match[2]))

    @classmethod
    def of(cls, day: date) -> Self:
        return cls(day.year, day.month)

    @property
    def first_day(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def last_day(self) -> date:
        return date(self.year, self.month, self.days)

    @property
    def days(self) -> int:
        return calendar.monthrange(self.year, self.month)[1]

    def shift(self, months: int) -> "Month":
        index = self.year * 12 + (self.month - 1) + months
        return Month(index // 12, index % 12 + 1)

    def contains(self, day: date) -> bool:
        return self.first_day <= day <= self.last_day

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"


def check_month(text: str | None) -> str | None:
    """For request validators: raises ValueError on anything that is not YYYY-MM."""
    if text is not None:
        Month.parse(text)

    return text
