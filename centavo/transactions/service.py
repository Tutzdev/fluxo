from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import ColumnElement, case, func, select
from sqlalchemy.orm import Session

from centavo.accounts.models import Account
from centavo.categories.models import Category
from centavo.categorization.service import CategorizationResult, CategorizationService
from centavo.imports.fingerprint import manual_fingerprint
from centavo.money import to_money
from centavo.month import Month
from centavo.ownership import get_owned
from centavo.text import normalize_description
from centavo.transactions.models import CategorySource, Transaction


@dataclass(frozen=True, slots=True)
class TransactionFilter:
    month: Month | None = None
    account_id: int | None = None
    category_id: int | None = None
    needs_review: bool | None = None
    search: str | None = None


@dataclass(frozen=True, slots=True)
class TransactionPage:
    items: Sequence[Transaction]
    total: int
    income: Decimal
    expenses: Decimal


@dataclass(frozen=True, slots=True)
class NewTransaction:
    account_id: int
    occurred_on: date
    description: str
    amount: Decimal
    category_id: int | None


class TransactionService:
    def __init__(self, session: Session, categorization: CategorizationService) -> None:
        self._session = session
        self._categorization = categorization

    def search(self, user_id: int, filters: TransactionFilter, page: int, page_size: int) -> TransactionPage:
        conditions = _conditions(user_id, filters)

        totals = self._session.execute(
            select(
                func.count(Transaction.id),
                func.coalesce(func.sum(case((Transaction.amount > 0, Transaction.amount))), 0),
                func.coalesce(func.sum(case((Transaction.amount < 0, Transaction.amount))), 0),
            ).where(*conditions)
        ).one()

        items = self._session.scalars(
            select(Transaction)
            .where(*conditions)
            .order_by(Transaction.occurred_on.desc(), Transaction.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()

        total, income, expenses = totals
        return TransactionPage(items=items, total=total, income=to_money(income), expenses=to_money(expenses))

    def create(self, user_id: int, new: NewTransaction) -> Transaction:
        """A transaction typed by hand. Without a category, rules and the model try first."""
        get_owned(self._session, Account, new.account_id, user_id)

        transaction = Transaction(
            user_id=user_id,
            account_id=new.account_id,
            occurred_on=new.occurred_on,
            description=new.description.strip(),
            normalized_description=normalize_description(new.description),
            amount=to_money(new.amount),
            fingerprint=manual_fingerprint(),
        )
        self._session.add(transaction)

        if new.category_id is None:
            self._categorization.categorize(user_id, [transaction])
        else:
            self._set_manual_category(user_id, transaction, new.category_id)

        self._session.commit()
        return transaction

    def change_category(self, user_id: int, transaction_id: int, category_id: int | None) -> Transaction:
        """The user's correction: it wins over rules and the model, and teaches the model."""
        transaction = get_owned(self._session, Transaction, transaction_id, user_id)

        if category_id is None:
            transaction.category_id = None
            transaction.category_source = None
            transaction.category_confidence = None
        else:
            self._set_manual_category(user_id, transaction, category_id)

        self._categorization.labels_changed(user_id)
        self._session.commit()
        return transaction

    def delete(self, user_id: int, transaction_id: int) -> None:
        transaction = get_owned(self._session, Transaction, transaction_id, user_id)

        self._session.delete(transaction)
        self._session.commit()

    def recategorize(self, user_id: int) -> CategorizationResult:
        result = self._categorization.recategorize_all(user_id)

        self._session.commit()
        return result

    def _set_manual_category(self, user_id: int, transaction: Transaction, category_id: int) -> None:
        get_owned(self._session, Category, category_id, user_id)

        transaction.category_id = category_id
        transaction.category_source = CategorySource.MANUAL
        transaction.category_confidence = None


def _conditions(user_id: int, filters: TransactionFilter) -> list[ColumnElement[bool]]:
    conditions = [Transaction.user_id == user_id]

    if filters.month is not None:
        conditions.append(Transaction.occurred_on.between(filters.month.first_day, filters.month.last_day))

    if filters.account_id is not None:
        conditions.append(Transaction.account_id == filters.account_id)

    if filters.category_id is not None:
        conditions.append(Transaction.category_id == filters.category_id)

    if filters.needs_review is True:
        conditions.append(Transaction.category_id.is_(None))
    elif filters.needs_review is False:
        conditions.append(Transaction.category_id.is_not(None))

    if filters.search:
        # Searching the normalized text makes "padaria" find "PADARIA SÃO JOÃO".
        text = normalize_description(filters.search)

        if text:
            conditions.append(Transaction.normalized_description.contains(text, autoescape=True))
        else:
            # Nothing with letters to normalize ("100%"): search the description as typed.
            conditions.append(Transaction.description.icontains(filters.search, autoescape=True))

    return conditions
