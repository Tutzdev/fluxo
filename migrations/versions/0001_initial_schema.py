"""Initial schema: users, accounts, categories, rules, imports, transactions and budgets.

Revision ID: 0001
Revises:
Create Date: 2026-11-15
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _id() -> sa.Column[int]:
    return sa.Column("id", sa.BigInteger(), primary_key=True)


def _user_id() -> sa.Column[int]:
    return sa.Column(
        "user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )


def _created_at() -> sa.Column[datetime]:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True, length=20)


def upgrade() -> None:
    op.create_table(
        "users",
        _id(),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("labels_version", sa.Integer(), server_default="0", nullable=False),
        _created_at(),
    )
    op.create_index("uq_users_email_lower", "users", [sa.literal_column("lower(email)")], unique=True)

    op.create_table(
        "auth_tokens",
        _id(),
        _user_id(),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        _created_at(),
    )
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"])

    op.create_table(
        "accounts",
        _id(),
        _user_id(),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("kind", _enum("accountkind", "checking", "savings", "credit_card", "cash"), nullable=False),
        sa.Column("opening_balance", sa.Numeric(14, 2), nullable=False),
        _created_at(),
    )
    op.create_index(
        "uq_accounts_user_id_name_lower",
        "accounts",
        ["user_id", sa.literal_column("lower(name)")],
        unique=True,
    )

    op.create_table(
        "categories",
        _id(),
        _user_id(),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("kind", _enum("categorykind", "expense", "income", "transfer"), nullable=False),
        sa.Column("color", sa.String(7), nullable=False),
        _created_at(),
    )
    op.create_index(
        "uq_categories_user_id_name_lower",
        "categories",
        ["user_id", sa.literal_column("lower(name)")],
        unique=True,
    )

    op.create_table(
        "category_rules",
        _id(),
        _user_id(),
        sa.Column(
            "category_id",
            sa.BigInteger(),
            sa.ForeignKey("categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pattern", sa.String(60), nullable=False),
        _created_at(),
        sa.UniqueConstraint("user_id", "pattern"),
    )
    op.create_index("ix_category_rules_category_id", "category_rules", ["category_id"])

    op.create_table(
        "imports",
        _id(),
        _user_id(),
        sa.Column(
            "account_id", sa.BigInteger(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_format", _enum("fileformat", "csv", "ofx"), nullable=False),
        sa.Column("imported_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("categorized_count", sa.Integer(), nullable=False),
        _created_at(),
    )
    op.create_index("ix_imports_user_id", "imports", ["user_id"])
    op.create_index("ix_imports_account_id", "imports", ["account_id"])

    op.create_table(
        "transactions",
        _id(),
        _user_id(),
        sa.Column(
            "account_id", sa.BigInteger(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("import_id", sa.BigInteger(), sa.ForeignKey("imports.id", ondelete="SET NULL")),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("description", sa.String(200), nullable=False),
        sa.Column("normalized_description", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("category_source", _enum("categorysource", "manual", "rule", "model")),
        sa.Column("category_confidence", sa.Numeric(4, 3)),
        sa.Column("fingerprint", sa.String(80), nullable=False),
        _created_at(),
        # The line that makes importing the same statement twice harmless.
        sa.UniqueConstraint("account_id", "fingerprint"),
    )
    op.create_index("ix_transactions_user_id_occurred_on", "transactions", ["user_id", "occurred_on"])
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])
    op.create_index("ix_transactions_import_id", "transactions", ["import_id"])

    op.create_table(
        "budgets",
        _id(),
        _user_id(),
        sa.Column(
            "category_id",
            sa.BigInteger(),
            sa.ForeignKey("categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("monthly_limit", sa.Numeric(14, 2), nullable=False),
        _created_at(),
        sa.UniqueConstraint("user_id", "category_id"),
        sa.CheckConstraint("monthly_limit > 0", name="monthly_limit_positive"),
    )
    op.create_index("ix_budgets_category_id", "budgets", ["category_id"])


def downgrade() -> None:
    for table in (
        "budgets",
        "transactions",
        "imports",
        "category_rules",
        "categories",
        "accounts",
        "auth_tokens",
    ):
        op.drop_table(table)

    op.drop_table("users")
