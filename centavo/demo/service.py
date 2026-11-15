"""A fresh, private demo account per visitor, built through the same services a real user goes through."""

import secrets
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from centavo.accounts.models import AccountKind
from centavo.accounts.service import AccountService
from centavo.auth.models import User
from centavo.auth.service import AuthService, IssuedToken
from centavo.budgets.service import BudgetService
from centavo.categories.models import Category
from centavo.categorization.service import CategorizationService
from centavo.clock import Clock
from centavo.demo.generator import generate, to_csv
from centavo.imports.service import ImportService
from centavo.transactions.models import Transaction
from centavo.transactions.service import TransactionService

DEMO_EMAIL_DOMAIN = "demo.centavo.app"
DEMO_LIFETIME = timedelta(hours=24)
DEMO_MONTHS = 6

# What the demo "user" teaches by hand: one correction each, the model does the rest.
TAUGHT = {
    "PREZUNIC TIJUCA": "Groceries",
    "BOTECO DO ZE": "Restaurants",
    "PIZZARIA BELLA NAPOLI": "Restaurants",
}

BUDGETS = {
    "Groceries": Decimal("1400"),
    "Restaurants": Decimal("700"),
    "Transport": Decimal("450"),
    "Shopping": Decimal("250"),
    "Leisure": Decimal("120"),
}


class DemoService:
    def __init__(
        self, session: Session, clock: Clock, auth: AuthService, categorization: CategorizationService
    ) -> None:
        self._session = session
        self._clock = clock
        self._auth = auth
        self._categorization = categorization

    def start(self) -> IssuedToken:
        self._delete_expired_demos()

        email = f"visitor-{secrets.token_hex(6)}@{DEMO_EMAIL_DOMAIN}"
        issued = self._auth.register("Demo visitor", email, secrets.token_urlsafe(24))
        user_id = issued.user.id

        self._import_statements(user_id)
        self._teach(user_id)
        self._set_budgets(user_id)

        return issued

    def _import_statements(self, user_id: int) -> None:
        accounts = AccountService(self._session)
        checking = accounts.create(user_id, "Nubank checking", AccountKind.CHECKING, Decimal("3200.00"))
        card = accounts.create(user_id, "Nubank card", AccountKind.CREDIT_CARD, Decimal("0.00"))

        statements = generate(self._clock.today(), DEMO_MONTHS)
        imports = ImportService(self._session, self._categorization)

        imports.import_statement(
            user_id, checking.account.id, "nubank-checking.csv", to_csv(statements.checking), False
        )
        imports.import_statement(user_id, card.account.id, "nubank-card.csv", to_csv(statements.card), False)

    def _teach(self, user_id: int) -> None:
        categories = self._categories_by_name(user_id)
        transactions = TransactionService(self._session, self._categorization)

        for description, category_name in TAUGHT.items():
            oldest = self._session.scalars(
                select(Transaction.id)
                .where(Transaction.user_id == user_id, Transaction.description == description)
                .order_by(Transaction.occurred_on)
                .limit(1)
            ).first()

            if oldest is not None:
                transactions.change_category(user_id, oldest, categories[category_name])

        transactions.recategorize(user_id)

    def _set_budgets(self, user_id: int) -> None:
        categories = self._categories_by_name(user_id)
        budgets = BudgetService(self._session)

        for category_name, limit in BUDGETS.items():
            budgets.set_limit(user_id, categories[category_name], limit)

    def _categories_by_name(self, user_id: int) -> dict[str, int]:
        rows = self._session.execute(select(Category.name, Category.id).where(Category.user_id == user_id))
        return dict(rows.all())

    def _delete_expired_demos(self) -> None:
        """Demo accounts live for a day; everything they own goes with them (ON DELETE CASCADE)."""
        self._session.execute(
            delete(User).where(
                User.email.like(f"%@{DEMO_EMAIL_DOMAIN}"),
                User.created_at < self._clock.now() - DEMO_LIFETIME,
            )
        )
        self._session.commit()
