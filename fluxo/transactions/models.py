import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from fluxo.database import Base, created_at_column, enum_column


class CategorySource(enum.StrEnum):
    """Who decided the category. Only MANUAL and RULE are trusted enough to train the model."""

    MANUAL = "manual"
    RULE = "rule"
    MODEL = "model"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    import_id: Mapped[int | None] = mapped_column(ForeignKey("imports.id", ondelete="SET NULL"), index=True)

    occurred_on: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(200))
    normalized_description: Mapped[str] = mapped_column(String(200))

    # Signed: negative is money leaving the account, positive is money coming in.
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    category_source: Mapped[CategorySource | None] = mapped_column(enum_column(CategorySource))
    category_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))

    # Identifies the same bank line across imports. See imports/fingerprint.py.
    fingerprint: Mapped[str] = mapped_column(String(80))

    created_at: Mapped[datetime] = created_at_column()

    __table_args__ = (
        UniqueConstraint(account_id, fingerprint),
        Index("ix_transactions_user_id_occurred_on", user_id, occurred_on),
    )

    @property
    def needs_review(self) -> bool:
        return self.category_id is None
