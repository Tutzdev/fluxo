"""Read-only views over the month: summary, trend and forecast.

Transfers between the user's own accounts are left out of every number here:
paying the card bill from checking is not spending, the purchases on the card were.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import ColumnElement, case, func, or_, select
from sqlalchemy.orm import Session

from centavo.accounts.service import AccountService
from centavo.categories.models import Category, CategoryKind
from centavo.money import to_money
from centavo.month import Month
from centavo.reports.forecast import Forecast, build_forecast
from centavo.reports.recurring import PastTransaction, find_recurring, series_key
from centavo.transactions.models import Transaction

HISTORY_MONTHS = 6
DAY_TO_DAY_WINDOW_DAYS = 90


@dataclass(frozen=True, slots=True)
class CategorySpending:
    category_id: int | None
    name: str
    color: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class MonthSummary:
    month: Month
    income: Decimal
    expenses: Decimal
    by_category: list[CategorySpending]
    needs_review: int

    @property
    def net(self) -> Decimal:
        return self.income - self.expenses


@dataclass(frozen=True, slots=True)
class MonthTotals:
    month: Month
    income: Decimal
    expenses: Decimal


class ReportService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def summary(self, user_id: int, month: Month) -> MonthSummary:
        in_month = Transaction.occurred_on.between(month.first_day, month.last_day)
        spent = (-func.sum(Transaction.amount)).label("spent")

        income, expenses, needs_review = self._session.execute(
            select(
                _sum_of(Transaction.amount > 0),
                _sum_of(Transaction.amount < 0),
                func.count().filter(Transaction.category_id.is_(None)),
            )
            .select_from(Transaction)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .where(Transaction.user_id == user_id, in_month, _not_a_transfer())
        ).one()

        by_category = self._session.execute(
            select(Category.id, Category.name, Category.color, spent)
            .select_from(Transaction)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .where(Transaction.user_id == user_id, in_month, Transaction.amount < 0, _not_a_transfer())
            .group_by(Category.id)
            .order_by(spent.desc())
        ).all()

        return MonthSummary(
            month=month,
            income=to_money(income),
            expenses=to_money(-expenses),
            by_category=[
                CategorySpending(
                    category_id=category_id,
                    name=name or "Needs review",
                    color=color or "#b8bec6",
                    amount=to_money(amount),
                )
                for category_id, name, color, amount in by_category
            ],
            needs_review=needs_review,
        )

    def trend(self, user_id: int, last_month: Month, months: int) -> list[MonthTotals]:
        """Income and expenses per month, oldest first; months without movement show as zero."""
        first_month = last_month.shift(-(months - 1))
        month_start = func.date_trunc("month", Transaction.occurred_on)

        rows = self._session.execute(
            select(month_start, _sum_of(Transaction.amount > 0), _sum_of(Transaction.amount < 0))
            .select_from(Transaction)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .where(
                Transaction.user_id == user_id,
                Transaction.occurred_on.between(first_month.first_day, last_month.last_day),
                _not_a_transfer(),
            )
            .group_by(month_start)
        ).all()

        totals = {Month.of(start): (income, expenses) for start, income, expenses in rows}
        result = []

        for offset in range(months):
            month = first_month.shift(offset)
            income, expenses = totals.get(month, (0, 0))
            result.append(MonthTotals(month=month, income=to_money(income), expenses=to_money(-expenses)))

        return result

    def forecast(self, user_id: int, today: date) -> Forecast:
        this_month = Month.of(today)
        history = self._history(
            user_id, this_month.shift(-HISTORY_MONTHS).first_day, this_month.shift(-1).last_day
        )
        recurring = find_recurring(history)

        this_month_so_far = self._history(user_id, this_month.first_day, today)
        already_seen = {series_key(item.normalized_description, item.amount) for item in this_month_so_far}

        balance_now = sum(
            (view.balance for view in AccountService(self._session).all(user_id)), start=Decimal(0)
        )

        return build_forecast(
            today=today,
            balance_now=to_money(balance_now),
            recurring=recurring,
            already_seen_this_month=already_seen,
            daily_spending=self._daily_spending(user_id, today, {series.key for series in recurring}),
        )

    def _daily_spending(self, user_id: int, today: date, recurring_keys: set[tuple[str, bool]]) -> Decimal:
        """Average day-to-day spending over the last 90 days (or since the first transaction)."""
        window_start = today - timedelta(days=DAY_TO_DAY_WINDOW_DAYS)
        history = self._history(user_id, window_start, today - timedelta(days=1))

        day_to_day = [
            item.amount
            for item in history
            if item.amount < 0 and series_key(item.normalized_description, item.amount) not in recurring_keys
        ]

        if not day_to_day:
            return Decimal("0")

        first_day = min(item.occurred_on for item in history)
        days_covered = max((today - first_day).days, 1)

        return sum(day_to_day, start=Decimal("0")) / days_covered

    def _history(self, user_id: int, first_day: date, last_day: date) -> list[PastTransaction]:
        rows = self._session.execute(
            select(
                Transaction.occurred_on,
                Transaction.description,
                Transaction.normalized_description,
                Transaction.amount,
                Transaction.category_id,
            )
            .select_from(Transaction)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .where(
                Transaction.user_id == user_id,
                Transaction.occurred_on.between(first_day, last_day),
                _not_a_transfer(),
            )
        ).all()

        return [
            PastTransaction(
                occurred_on=row.occurred_on,
                description=row.description,
                normalized_description=row.normalized_description,
                amount=row.amount,
                category_id=row.category_id,
            )
            for row in rows
        ]


def _not_a_transfer() -> ColumnElement[bool]:
    return or_(Category.kind.is_(None), Category.kind != CategoryKind.TRANSFER)


def _sum_of(condition: ColumnElement[bool]) -> ColumnElement[Decimal]:
    return func.coalesce(func.sum(case((condition, Transaction.amount))), 0)
