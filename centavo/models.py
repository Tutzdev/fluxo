"""Imports every model so the metadata is complete (Alembic and the app both rely on it)."""

from centavo.accounts.models import Account, AccountKind
from centavo.auth.models import AuthToken, User
from centavo.budgets.models import Budget
from centavo.categories.models import Category, CategoryKind, CategoryRule
from centavo.imports.models import FileFormat, StatementImport
from centavo.transactions.models import CategorySource, Transaction

__all__ = [
    "Account",
    "AccountKind",
    "AuthToken",
    "Budget",
    "Category",
    "CategoryKind",
    "CategoryRule",
    "CategorySource",
    "FileFormat",
    "StatementImport",
    "Transaction",
    "User",
]
