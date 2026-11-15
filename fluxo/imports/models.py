import enum
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from fluxo.database import Base, created_at_column, enum_column


class FileFormat(enum.StrEnum):
    CSV = "csv"
    OFX = "ofx"


class StatementImport(Base):
    """One uploaded statement file and what came out of it."""

    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_format: Mapped[FileFormat] = mapped_column(enum_column(FileFormat))
    imported_count: Mapped[int]
    duplicate_count: Mapped[int]
    categorized_count: Mapped[int]
    created_at: Mapped[datetime] = created_at_column()
