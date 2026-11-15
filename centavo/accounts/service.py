from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from centavo.accounts.models import Account, AccountKind
from centavo.errors import ConflictError
from centavo.money import to_money
from centavo.ownership import get_owned
from centavo.transactions.models import Transaction


@dataclass(frozen=True, slots=True)
class AccountView:
    account: Account
    balance: Decimal
    transaction_count: int


class AccountService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def all(self, user_id: int) -> list[AccountView]:
        return self._views(user_id)

    def get(self, user_id: int, account_id: int) -> AccountView:
        get_owned(self._session, Account, account_id, user_id)
        return self._views(user_id, account_id)[0]

    def create(self, user_id: int, name: str, kind: AccountKind, opening_balance: Decimal) -> AccountView:
        account = Account(user_id=user_id, name=name, kind=kind, opening_balance=to_money(opening_balance))
        self._session.add(account)

        self._flush_unique_name()
        self._session.commit()
        return self.get(user_id, account.id)

    def rename(self, user_id: int, account_id: int, name: str) -> AccountView:
        account = get_owned(self._session, Account, account_id, user_id)
        account.name = name

        self._flush_unique_name()
        self._session.commit()
        return self.get(user_id, account_id)

    def delete(self, user_id: int, account_id: int) -> None:
        """Deleting an account deletes its transactions and imports too (the client confirms first)."""
        account = get_owned(self._session, Account, account_id, user_id)

        self._session.delete(account)
        self._session.commit()

    def _views(self, user_id: int, account_id: int | None = None) -> list[AccountView]:
        """Accounts with their balance (opening balance plus every transaction), in one query."""
        movements = func.coalesce(func.sum(Transaction.amount), 0)
        statement = (
            select(Account, movements, func.count(Transaction.id))
            .outerjoin(Transaction, Transaction.account_id == Account.id)
            .where(Account.user_id == user_id)
            .group_by(Account.id)
            .order_by(Account.name)
        )

        if account_id is not None:
            statement = statement.where(Account.id == account_id)

        return [
            AccountView(
                account=account, balance=to_money(account.opening_balance + total), transaction_count=count
            )
            for account, total, count in self._session.execute(statement).all()
        ]

    def _flush_unique_name(self) -> None:
        try:
            self._session.flush()
        except IntegrityError as error:
            self._session.rollback()
            raise ConflictError(
                "ACCOUNT_NAME_TAKEN", "You already have an account with this name."
            ) from error
