from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from centavo.imports.models import FileFormat
from centavo.imports.parsers.base import StatementFormatError
from centavo.imports.parsers.ofx_parser import parse_ofx
from centavo.imports.reader import read_statement

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_reads_sgml_ofx_without_closing_tags_in_windows_1252():
    statement = read_statement((FIXTURES / "itau-sgml.ofx").read_bytes())

    assert statement.file_format is FileFormat.OFX
    assert [(line.occurred_on, line.amount, line.external_id) for line in statement.lines] == [
        (date(2026, 11, 5), Decimal("-120.50"), "2026110501"),
        (date(2026, 11, 6), Decimal("1000.00"), "2026110601"),
    ]
    assert statement.lines[1].description == "SALÁRIO ACME"


def test_reads_xml_ofx_and_falls_back_to_name_without_memo():
    statement = read_statement((FIXTURES / "bank-xml.ofx").read_bytes())

    assert statement.lines[0].description == "ALURA CURSOS"
    assert statement.lines[0].amount == Decimal("-89.90")


def test_a_file_without_transactions_is_an_error():
    with pytest.raises(StatementFormatError, match="No transactions"):
        parse_ofx("<OFX><BANKTRANLIST></BANKTRANLIST></OFX>")


def test_says_which_transaction_is_broken():
    with pytest.raises(StatementFormatError, match="Transaction 1: no TRNAMT"):
        parse_ofx("<OFX><STMTTRN><DTPOSTED>20261101<MEMO>X</BANKTRANLIST></OFX>")


def test_an_empty_upload_is_an_error():
    with pytest.raises(StatementFormatError, match="empty"):
        read_statement(b"  \n")
