"""Importing a statement: read, skip what is already there, categorize what is new."""

from collections.abc import Sequence
from dataclasses import replace

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from centavo.accounts.models import Account
from centavo.categorization.service import CategorizationService
from centavo.errors import InvalidInputError
from centavo.imports.fingerprint import fingerprint_lines
from centavo.imports.models import StatementImport
from centavo.imports.parsers.base import StatementFormatError, StatementLine
from centavo.imports.reader import ReadStatement, read_statement
from centavo.ownership import get_owned
from centavo.text import normalize_description
from centavo.transactions.models import Transaction

MAX_LINES_PER_FILE = 5000
MAX_DESCRIPTION_LENGTH = 200
RECENT_IMPORTS = 20


class ImportService:
    def __init__(self, session: Session, categorization: CategorizationService) -> None:
        self._session = session
        self._categorization = categorization

    def import_statement(
        self,
        user_id: int,
        account_id: int,
        filename: str,
        content: bytes,
        invert_amounts: bool,
    ) -> StatementImport:
        """Safe to run twice with the same file: the second run imports nothing.

        invert_amounts is for credit card exports that list purchases as
        positive numbers; everywhere in Centavo money going out is negative.
        """
        get_owned(self._session, Account, account_id, user_id)
        statement = self._read(content)
        lines = [_inverted(line) for line in statement.lines] if invert_amounts else statement.lines

        statement_import = StatementImport(
            user_id=user_id,
            account_id=account_id,
            filename=filename[:255],
            file_format=statement.file_format,
            imported_count=0,
            duplicate_count=0,
            categorized_count=0,
        )
        self._session.add(statement_import)
        self._session.flush()

        new_ids = self._insert_new_lines(user_id, account_id, statement_import.id, lines)
        new_transactions = self._session.scalars(select(Transaction).where(Transaction.id.in_(new_ids))).all()
        categorization = self._categorization.categorize(user_id, new_transactions)

        statement_import.imported_count = len(new_ids)
        statement_import.duplicate_count = len(lines) - len(new_ids)
        statement_import.categorized_count = categorization.categorized

        self._session.commit()
        return statement_import

    def recent(self, user_id: int) -> Sequence[StatementImport]:
        statement = (
            select(StatementImport)
            .where(StatementImport.user_id == user_id)
            .order_by(StatementImport.created_at.desc(), StatementImport.id.desc())
            .limit(RECENT_IMPORTS)
        )
        return self._session.scalars(statement).all()

    def _read(self, content: bytes) -> ReadStatement:
        try:
            statement = read_statement(content)
        except StatementFormatError as error:
            raise InvalidInputError("UNREADABLE_STATEMENT", str(error)) from error

        if not statement.lines:
            raise InvalidInputError("EMPTY_STATEMENT", "The file has no transactions.")

        if len(statement.lines) > MAX_LINES_PER_FILE:
            raise InvalidInputError(
                "STATEMENT_TOO_LONG", f"Split the file: at most {MAX_LINES_PER_FILE} lines."
            )

        return statement

    def _insert_new_lines(
        self,
        user_id: int,
        account_id: int,
        import_id: int,
        lines: Sequence[StatementLine],
    ) -> list[int]:
        """One INSERT ... ON CONFLICT DO NOTHING: the database, not a prior SELECT, decides what is new.

        A SELECT-then-INSERT would let two uploads of the same file, at the
        same moment, both see "not there yet" and both insert.
        """
        rows = [
            {
                "user_id": user_id,
                "account_id": account_id,
                "import_id": import_id,
                "occurred_on": line.occurred_on,
                "description": _description(line),
                "normalized_description": normalize_description(_description(line)),
                "amount": line.amount,
                "fingerprint": fingerprint,
            }
            for line, fingerprint in zip(lines, fingerprint_lines(lines), strict=True)
        ]

        statement = (
            insert(Transaction)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["account_id", "fingerprint"])
            .returning(Transaction.id)
        )
        return list(self._session.scalars(statement))


def _inverted(line: StatementLine) -> StatementLine:
    return replace(line, amount=-line.amount)


def _description(line: StatementLine) -> str:
    return line.description[:MAX_DESCRIPTION_LENGTH] or "(no description)"
