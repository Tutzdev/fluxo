from datetime import date
from decimal import Decimal

from centavo.reports.forecast import build_forecast
from centavo.reports.recurring import RecurringSeries


def series(description, amount, day):
    return RecurringSeries(description, description, Decimal(amount), day, None, 3)


SALARY = series("SALARIO", "6800.00", 5)
RENT = series("ALUGUEL", "-1850.00", 10)
INTERNET = series("CLARO", "-109.90", 20)


def test_adds_what_is_still_to_come_and_the_usual_pace_for_the_days_left():
    forecast = build_forecast(
        today=date(2026, 11, 15),
        balance_now=Decimal("5000.00"),
        recurring=[SALARY, RENT, INTERNET],
        already_seen_this_month={SALARY.key, RENT.key},
        daily_spending=Decimal("-80"),
    )

    assert forecast.days_left == 15
    assert forecast.upcoming == [INTERNET]
    assert forecast.expected_income == Decimal("0.00")
    assert forecast.expected_bills == Decimal("-109.90")
    assert forecast.projected_day_to_day == Decimal("-1200.00")
    assert forecast.projected_end_balance == Decimal("3690.10")


def test_on_the_last_day_only_the_balance_and_what_is_missing_count():
    forecast = build_forecast(
        today=date(2026, 11, 30),
        balance_now=Decimal("100.00"),
        recurring=[SALARY],
        already_seen_this_month=set(),
        daily_spending=Decimal("-80"),
    )

    assert forecast.days_left == 0
    assert forecast.projected_end_balance == Decimal("6900.00")
