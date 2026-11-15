"""Imports every model so the metadata is complete (Alembic and the app both rely on it)."""

from fluxo.accounts.models import Account, AccountKind
from fluxo.auth.models import AuthToken, User
from fluxo.budgets.models import Budget
from fluxo.categories.models import Category, CategoryKind, CategoryRule
from fluxo.imports.models import FileFormat, StatementImport
from fluxo.transactions.models import CategorySource, Transaction

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
