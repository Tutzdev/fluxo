from decimal import Decimal

import pytest

from fluxo.money import parse_amount, to_money


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("-45.90", "-45.90"),
        ("-45,90", "-45.90"),
        ("1.234,56", "1234.56"),
        ("1,234.56", "1234.56"),
        ("R$ -1.000,00", "-1000.00"),
        ("3500", "3500.00"),
    ],
)
def test_reads_brazilian_and_international_amounts(raw, expected):
    assert parse_amount(raw) == Decimal(expected)


@pytest.mark.parametrize("raw", ["", "R$", "abc", "12-3"])
def test_rejects_text_that_is_not_an_amount(raw):
    with pytest.raises(ValueError):
        parse_amount(raw)


def test_rounds_half_to_even_like_banks_do():
    assert to_money("2.345") == Decimal("2.34")
    assert to_money("2.355") == Decimal("2.36")
