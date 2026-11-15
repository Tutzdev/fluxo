"""Spots the bills and incomes that come back every month: rent, salary, Netflix."""

import statistics
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from fluxo.money import to_money
from fluxo.month import Month

MIN_MONTHS = 3
AMOUNT_TOLERANCE = Decimal("0.20")


def series_key(normalized_description: str, amount: Decimal) -> tuple[str, bool]:
    """Same text and same direction: a refund from Netflix is not the Netflix bill."""
    return normalized_description, amount > 0


@dataclass(frozen=True, slots=True)
class PastTransaction:
    occurred_on: date
    description: str
    normalized_description: str
    amount: Decimal
    category_id: int | None


@dataclass(frozen=True, slots=True)
class RecurringSeries:
    description: str
    normalized_description: str
    typical_amount: Decimal
    typical_day: int
    category_id: int | None
    months_seen: int

    @property
    def key(self) -> tuple[str, bool]:
        return series_key(self.normalized_description, self.typical_amount)


def find_recurring(history: Sequence[PastTransaction]) -> list[RecurringSeries]:
    """A series is recurring when it shows up in at least MIN_MONTHS different months,
    at most once a month, always for about the same amount (within AMOUNT_TOLERANCE).

    'Once a month' keeps out the places you simply go often: ten Uber rides a
    month are spending habits, not a bill with a due date.
    """
    groups: dict[tuple[str, bool], list[PastTransaction]] = defaultdict(list)

    for item in history:
        groups[series_key(item.normalized_description, item.amount)].append(item)

    found = []

    for group in groups.values():
        series = _as_series(group)

        if series is not None:
            found.append(series)

    return sorted(found, key=lambda series: series.typical_day)


def _as_series(group: list[PastTransaction]) -> RecurringSeries | None:
    months = {Month.of(item.occurred_on) for item in group}

    if len(months) < MIN_MONTHS or len(group) > len(months):
        return None

    amounts = [item.amount for item in group]
    typical_amount = to_money(statistics.median(amounts))
    tolerance = abs(typical_amount) * AMOUNT_TOLERANCE

    if any(abs(amount - typical_amount) > tolerance for amount in amounts):
        return None

    latest = max(group, key=lambda item: item.occurred_on)

    return RecurringSeries(
        description=latest.description,
        normalized_description=latest.normalized_description,
        typical_amount=typical_amount,
        typical_day=int(statistics.median(item.occurred_on.day for item in group)),
        category_id=latest.category_id,
        months_seen=len(months),
    )
