"""CSV statements: Nubank (account and card), most Brazilian banks, and generic exports.

Columns are found by name, in English or Portuguese, so the order does not matter.
"""

import csv
import io
import unicodedata
from datetime import date, datetime

from fluxo.imports.parsers.base import StatementFormatError, StatementLine
from fluxo.money import parse_amount

DATE_COLUMNS = {"date", "data", "data lancamento", "data de lancamento"}
DESCRIPTION_COLUMNS = {"description", "descricao", "title", "titulo", "historico", "lancamento"}
AMOUNT_COLUMNS = {"amount", "value", "valor", "valor (r$)"}
ID_COLUMNS = {"id", "identificador", "fitid"}

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y")


def parse_csv(text: str) -> list[StatementLine]:
    rows = _read_rows(text)
    header, body = rows[0], rows[1:]

    date_index = _find_column(header, DATE_COLUMNS, "date")
    description_index = _find_column(header, DESCRIPTION_COLUMNS, "description")
    amount_index = _find_column(header, AMOUNT_COLUMNS, "amount")
    id_index = _find_optional_column(header, ID_COLUMNS)

    lines = []

    for line_number, row in enumerate(body, start=2):
        if not any(cell.strip() for cell in row):
            continue

        try:
            lines.append(
                StatementLine(
                    occurred_on=_parse_date(row[date_index]),
                    description=row[description_index].strip(),
                    amount=parse_amount(row[amount_index]),
                    external_id=_optional_cell(row, id_index),
                )
            )
        except (ValueError, IndexError) as error:
            raise StatementFormatError(f"Line {line_number}: {error}") from error

    return lines


def _read_rows(text: str) -> list[list[str]]:
    sample = text[:4096]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error as error:
        raise StatementFormatError("Could not tell how the columns are separated.") from error

    rows = list(csv.reader(io.StringIO(text), dialect))

    if len(rows) < 2:
        raise StatementFormatError("The file has no lines after the header.")

    return rows


def _find_column(header: list[str], names: set[str], label: str) -> int:
    index = _find_optional_column(header, names)

    if index is None:
        raise StatementFormatError(f"No {label} column. Expected one of: {', '.join(sorted(names))}.")

    return index


def _find_optional_column(header: list[str], names: set[str]) -> int | None:
    for index, column in enumerate(header):
        if _column_key(column) in names:
            return index

    return None


def _column_key(column: str) -> str:
    """' Descrição' -> 'descricao'. NFKD + ASCII also drops the byte order mark Excel adds."""
    without_accents = unicodedata.normalize("NFKD", column).encode("ascii", "ignore").decode()
    return without_accents.strip().lower()


def _optional_cell(row: list[str], index: int | None) -> str | None:
    if index is None:
        return None

    return row[index].strip() or None


def _parse_date(raw: str) -> date:
    text = raw.strip()

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue

    raise ValueError(f"Not a date: {raw!r}")
