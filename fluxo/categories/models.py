import enum
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from fluxo.database import Base, created_at_column, enum_column


class CategoryKind(enum.StrEnum):
    EXPENSE = "expense"
    INCOME = "income"

    # Money moving between the user's own accounts (paying the credit card
    # bill, saving). Counting it as spending would count the same money twice.
    TRANSFER = "transfer"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(40))
    kind: Mapped[CategoryKind] = mapped_column(enum_column(CategoryKind))
    color: Mapped[str] = mapped_column(String(7))
    created_at: Mapped[datetime] = created_at_column()

    __table_args__ = (Index("uq_categories_user_id_name_lower", user_id, func.lower(name), unique=True),)


class CategoryRule(Base):
    """'If the description contains PATTERN, it is CATEGORY.' The user's explicit word beats the model."""

    __tablename__ = "category_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True)
    pattern: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime] = created_at_column()

    __table_args__ = (UniqueConstraint(user_id, pattern),)
