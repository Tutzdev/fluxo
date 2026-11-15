"""Where the balance will be at the end of the month, if the month keeps its usual pace.

end balance = balance today
            + recurring incomes and bills still to come this month
            + usual day-to-day spending x days left
"""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from fluxo.money import to_money
from fluxo.month import Month
from fluxo.reports.recurring import RecurringSeries

ZERO = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class Forecast:
    today: date
    days_left: int
    balance_now: Decimal
    upcoming: list[RecurringSeries]
    expected_income: Decimal
    expected_bills: Decimal
    projected_day_to_day: Decimal
    projected_end_balance: Decimal


def build_forecast(
    today: date,
    balance_now: Decimal,
    recurring: Sequence[RecurringSeries],
    already_seen_this_month: Collection[tuple[str, bool]],
    daily_spending: Decimal,
) -> Forecast:
    """daily_spending is negative (money going out per day), recurring bills excluded."""
    days_left = (Month.of(today).last_day - today).days
    upcoming = [series for series in recurring if series.key not in already_seen_this_month]

    expected_income = sum((s.typical_amount for s in upcoming if s.typical_amount > 0), start=ZERO)
    expected_bills = sum((s.typical_amount for s in upcoming if s.typical_amount < 0), start=ZERO)
    projected_day_to_day = to_money(daily_spending * days_left)

    return Forecast(
        today=today,
        days_left=days_left,
        balance_now=balance_now,
        upcoming=upcoming,
        expected_income=expected_income,
        expected_bills=expected_bills,
        projected_day_to_day=projected_day_to_day,
        projected_end_balance=balance_now + expected_income + expected_bills + projected_day_to_day,
    )
