import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from fluxo.database import Base, created_at_column, enum_column


class AccountKind(enum.StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    CASH = "cash"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(60))
    kind: Mapped[AccountKind] = mapped_column(enum_column(AccountKind))
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = created_at_column()

    __table_args__ = (Index("uq_accounts_user_id_name_lower", user_id, func.lower(name), unique=True),)
