from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from centavo.database import Base, created_at_column


class Budget(Base):
    """A monthly spending limit for one expense category. The same limit applies every month."""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True)
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = created_at_column()

    __table_args__ = (
        UniqueConstraint(user_id, category_id),
        CheckConstraint("monthly_limit > 0", name="monthly_limit_positive"),
    )
