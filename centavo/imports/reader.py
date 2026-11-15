"""From uploaded bytes to statement lines, whatever the bank and the encoding."""

from dataclasses import dataclass

from centavo.imports.models import FileFormat
from centavo.imports.parsers.base import StatementFormatError, StatementLine
from centavo.imports.parsers.csv_parser import parse_csv
from centavo.imports.parsers.ofx_parser import looks_like_ofx, parse_ofx


@dataclass(frozen=True, slots=True)
class ReadStatement:
    file_format: FileFormat
    lines: list[StatementLine]


def read_statement(content: bytes) -> ReadStatement:
    text = _decode(content)

    if looks_like_ofx(text):
        return ReadStatement(FileFormat.OFX, parse_ofx(text))

    return ReadStatement(FileFormat.CSV, parse_csv(text))


def _decode(content: bytes) -> str:
    """UTF-8 first (with or without BOM); Brazilian OFX files are often Windows-1252."""
    if not content.strip():
        raise StatementFormatError("The file is empty.")

    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("cp1252", errors="replace")
