from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import and_, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from centavo.budgets.models import Budget
from centavo.budgets.status import BudgetStatus, budget_status
from centavo.categories.models import Category, CategoryKind
from centavo.errors import InvalidInputError, NotFoundError
from centavo.money import to_money
from centavo.month import Month
from centavo.ownership import get_owned
from centavo.transactions.models import Transaction


@dataclass(frozen=True, slots=True)
class BudgetProgress:
    category: Category
    monthly_limit: Decimal
    spent: Decimal
    status: BudgetStatus

    @property
    def remaining(self) -> Decimal:
        return self.monthly_limit - self.spent

    @property
    def percent_used(self) -> int:
        return int(self.spent * 100 / self.monthly_limit)


class BudgetService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def progress(self, user_id: int, month: Month) -> list[BudgetProgress]:
        """Each budget next to what was spent in its category that month, in one query."""
        spent = func.coalesce(-func.sum(Transaction.amount), 0)
        in_month_spending = and_(
            Transaction.category_id == Budget.category_id,
            Transaction.amount < 0,
            Transaction.occurred_on.between(month.first_day, month.last_day),
        )

        statement = (
            select(Budget, Category, spent)
            .join(Category, Category.id == Budget.category_id)
            .outerjoin(Transaction, in_month_spending)
            .where(Budget.user_id == user_id)
            .group_by(Budget.id, Category.id)
            .order_by(Category.name)
        )

        return [
            BudgetProgress(
                category=category,
                monthly_limit=budget.monthly_limit,
                spent=to_money(amount),
                status=budget_status(budget.monthly_limit, to_money(amount)),
            )
            for budget, category, amount in self._session.execute(statement).all()
        ]

    def set_limit(self, user_id: int, category_id: int, monthly_limit: Decimal) -> None:
        """Creates or replaces the budget (an upsert, so two clicks never make two budgets)."""
        category = get_owned(self._session, Category, category_id, user_id)

        if category.kind is not CategoryKind.EXPENSE:
            raise InvalidInputError(
                "NOT_AN_EXPENSE_CATEGORY", "Budgets only make sense for expense categories."
            )

        statement = (
            insert(Budget)
            .values(user_id=user_id, category_id=category_id, monthly_limit=to_money(monthly_limit))
            .on_conflict_do_update(
                index_elements=["user_id", "category_id"],
                set_={"monthly_limit": to_money(monthly_limit)},
            )
        )
        self._session.execute(statement)
        self._session.commit()

    def remove(self, user_id: int, category_id: int) -> None:
        deleted = self._session.scalars(
            delete(Budget)
            .where(Budget.user_id == user_id, Budget.category_id == category_id)
            .returning(Budget.id)
        ).first()

        if deleted is None:
            raise NotFoundError("BUDGET_NOT_FOUND", f"No budget for category {category_id}.")

        self._session.commit()
