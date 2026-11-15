from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class StatementLine:
    """One line of a bank statement, whatever the file format was."""

    occurred_on: date
    description: str
    amount: Decimal

    # The bank's own id for the line (OFX FITID, Nubank 'Identificador'), when it gives one.
    external_id: str | None = None


class StatementFormatError(ValueError):
    """The file could not be read as a statement. The message says where and why."""
