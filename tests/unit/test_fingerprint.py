from datetime import date
from decimal import Decimal

from fluxo.imports.fingerprint import fingerprint_lines, manual_fingerprint
from fluxo.imports.parsers.base import StatementLine


def line(day, description, amount, external_id=None):
    return StatementLine(date(2026, 11, day), description, Decimal(amount), external_id)


def test_the_same_file_always_gets_the_same_fingerprints():
    lines = [line(1, "PADARIA", "-10"), line(2, "UBER", "-20")]

    assert fingerprint_lines(lines) == fingerprint_lines(list(lines))


def test_two_real_identical_purchases_on_the_same_day_stay_apart():
    first, second = fingerprint_lines([line(3, "CAFE", "-6.50"), line(3, "CAFE", "-6.50")])

    assert first != second


def test_overlapping_exports_give_shared_lines_the_same_fingerprint():
    first_export = [line(1, "CAFE", "-6.50"), line(1, "CAFE", "-6.50"), line(10, "UBER", "-20")]
    second_export = [*first_export, line(14, "IFOOD", "-50")]

    assert set(fingerprint_lines(first_export)) <= set(fingerprint_lines(second_export))


def test_descriptions_that_only_differ_in_noise_are_the_same_line():
    [a] = fingerprint_lines([line(5, "Uber *Trip 05/11", "-20")])
    [b] = fingerprint_lines([line(5, "UBER TRIP 05/11", "-20")])

    assert a == b


def test_the_bank_id_wins_when_the_bank_sends_one():
    [a] = fingerprint_lines([line(5, "UBER", "-20", external_id="FIT-1")])
    [b] = fingerprint_lines([line(6, "Uber corrected", "-21", external_id="FIT-1")])

    assert a == b
    assert a.startswith("id:")


def test_manual_transactions_never_collide():
    assert manual_fingerprint() != manual_fingerprint()
