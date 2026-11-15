from datetime import date
from decimal import Decimal

from centavo.reports.recurring import PastTransaction, find_recurring


def paid(month, day, description, amount):
    return PastTransaction(date(2026, month, day), description, description, Decimal(amount), None)


def test_a_bill_paid_every_month_for_about_the_same_amount_is_recurring():
    history = [paid(7, 15, "ENEL", "-180.00"), paid(8, 14, "ENEL", "-195.10"), paid(9, 16, "ENEL", "-172.30")]

    [series] = find_recurring(history)

    assert series.normalized_description == "ENEL"
    assert series.typical_amount == Decimal("-180.00")
    assert series.typical_day == 15
    assert series.months_seen == 3


def test_two_months_are_not_enough():
    assert find_recurring([paid(8, 10, "ALUGUEL", "-1850"), paid(9, 10, "ALUGUEL", "-1850")]) == []


def test_somewhere_you_go_often_is_a_habit_not_a_bill():
    history = [paid(month, day, "UBER", "-20") for month in (7, 8, 9) for day in (3, 12, 25)]

    assert find_recurring(history) == []


def test_an_amount_that_jumps_around_is_not_a_bill():
    history = [paid(7, 5, "LOJA X", "-50"), paid(8, 5, "LOJA X", "-300"), paid(9, 5, "LOJA X", "-52")]

    assert find_recurring(history) == []


def test_income_and_refunds_from_the_same_place_are_separate_series():
    bills = [paid(month, 8, "NETFLIX", "-55.90") for month in (7, 8, 9)]
    refund = [paid(9, 20, "NETFLIX", "55.90")]

    [series] = find_recurring(bills + refund)

    assert series.typical_amount == Decimal("-55.90")
