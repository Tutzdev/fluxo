from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from fluxo.imports.parsers.base import StatementFormatError
from fluxo.imports.parsers.csv_parser import parse_csv

FIXTURES = Path(__file__).parent.parent / "fixtures"


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_reads_a_nubank_checking_export_with_its_ids():
    lines = parse_csv(read("nubank-checking.csv"))

    assert len(lines) == 3
    assert lines[0].occurred_on == date(2026, 11, 1)
    assert lines[0].description == "Compra no débito - Padaria Bela Vista"
    assert lines[0].amount == Decimal("-45.90")
    assert lines[0].external_id == "6544a1f0-0001"


def test_reads_a_nubank_card_export_as_it_comes():
    lines = parse_csv(read("nubank-card.csv"))

    assert [line.amount for line in lines] == [
        Decimal("58.90"),
        Decimal("23.45"),
        Decimal("55.90"),
        Decimal("-1500.00"),
    ]
    assert all(line.external_id is None for line in lines)


def test_finds_columns_by_name_with_semicolons_and_brazilian_amounts():
    lines = parse_csv("Histórico;Valor;Data\nPADARIA;-1.234,56;05/11/2026\n")

    assert lines[0].description == "PADARIA"
    assert lines[0].amount == Decimal("-1234.56")
    assert lines[0].occurred_on == date(2026, 11, 5)


def test_skips_blank_lines():
    lines = parse_csv("date,description,amount\n2026-11-01,A,-1\n,,\n2026-11-02,B,-2\n")

    assert [line.description for line in lines] == ["A", "B"]


def test_says_which_column_is_missing():
    with pytest.raises(StatementFormatError, match="No amount column"):
        parse_csv("date,description\n2026-11-01,PADARIA\n")


def test_says_which_line_is_broken():
    with pytest.raises(StatementFormatError, match="Line 3"):
        parse_csv("date,description,amount\n2026-11-01,A,-1\n31/31/2026,B,-2\n")
