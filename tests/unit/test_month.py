from datetime import date

import pytest

from fluxo.month import Month


def test_parses_year_and_month():
    assert Month.parse("2026-11") == Month(2026, 11)


@pytest.mark.parametrize("text", ["2026-13", "2026-00", "26-11", "2026/11", "november"])
def test_rejects_anything_else(text):
    with pytest.raises(ValueError):
        Month.parse(text)


def test_shifts_across_years():
    assert Month(2026, 11).shift(3) == Month(2027, 2)
    assert Month(2026, 1).shift(-1) == Month(2025, 12)
    assert Month(2026, 6).shift(-18) == Month(2024, 12)


def test_knows_its_last_day_including_leap_years():
    assert Month(2028, 2).last_day == date(2028, 2, 29)
    assert Month(2026, 2).last_day == date(2026, 2, 28)


def test_prints_as_year_dash_month():
    assert str(Month(2026, 3)) == "2026-03"
