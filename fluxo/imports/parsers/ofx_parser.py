"""OFX statements, the format every Brazilian bank exports.

Most of them still send OFX 1.x, which is SGML: closing tags are optional
('<TRNAMT>-45.90' with no '</TRNAMT>'). An XML parser chokes on that, so each
<STMTTRN> block is read field by field instead.
"""

import re
from datetime import date

from fluxo.imports.parsers.base import StatementFormatError, StatementLine
from fluxo.money import parse_amount

_TRANSACTION_BLOCK = re.compile(
    r"<STMTTRN>(.*?)(?=</STMTTRN>|<STMTTRN>|</BANKTRANLIST>)", re.DOTALL | re.IGNORECASE
)
_FIELD = r"<{name}>([^<\r\n]+)"
_OFX_DATE = re.compile(r"^(\d{4})(\d{2})(\d{2})")


def looks_like_ofx(text: str) -> bool:
    return "<OFX>" in text.upper()


def parse_ofx(text: str) -> list[StatementLine]:
    blocks = _TRANSACTION_BLOCK.findall(text)

    if not blocks:
        raise StatementFormatError("No transactions (<STMTTRN>) in this OFX file.")

    lines = []

    for position, block in enumerate(blocks, start=1):
        try:
            lines.append(_parse_block(block))
        except ValueError as error:
            raise StatementFormatError(f"Transaction {position}: {error}") from error

    return lines


def _parse_block(block: str) -> StatementLine:
    description = _field(block, "MEMO") or _field(block, "NAME")

    if description is None:
        raise ValueError("no MEMO or NAME")

    return StatementLine(
        occurred_on=_parse_date(_required_field(block, "DTPOSTED")),
        description=description,
        amount=parse_amount(_required_field(block, "TRNAMT")),
        external_id=_field(block, "FITID"),
    )


def _field(block: str, name: str) -> str | None:
    match = re.search(_FIELD.format(name=name), block, re.IGNORECASE)
    return match[1].strip() if match else None


def _required_field(block: str, name: str) -> str:
    value = _field(block, name)

    if value is None:
        raise ValueError(f"no {name}")

    return value


def _parse_date(raw: str) -> date:
    """'20261112', '20261112120000' and '20261112120000[-3:BRT]' are all 2026-11-12."""
    match = _OFX_DATE.match(raw)

    if match is None:
        raise ValueError(f"not a date: {raw!r}")

    return date(int(match[1]), int(match[2]), int(match[3]))
