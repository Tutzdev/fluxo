from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from centavo.database import Base, created_at_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(254))
    name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(255))

    # Bumped whenever the user teaches a category (a correction or a rule),
    # so a cached classifier knows it is out of date.
    labels_version: Mapped[int] = mapped_column(default=0, server_default="0")

    created_at: Mapped[datetime] = created_at_column()

    __table_args__ = (Index("uq_users_email_lower", func.lower(email), unique=True),)


class AuthToken(Base):
    """An opaque bearer token. Only its SHA-256 is stored, so a database leak leaks no sessions."""

    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at_column()
