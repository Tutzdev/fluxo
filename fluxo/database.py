"""SQLAlchemy setup: one engine per app, one session per request."""

import enum
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from flask import Flask, current_app, g
from sqlalchemy import DateTime, Enum, MetaData, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def created_at_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


def enum_column[E: enum.StrEnum](enum_class: type[E]) -> Enum:
    """Stores a StrEnum by value in a VARCHAR guarded by a CHECK, not as a native Postgres enum.

    Adding a value to a CHECK is a plain migration; altering a native enum is not.
    """
    return Enum(
        enum_class,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda members: [member.value for member in members],
    )


class Database:
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url, pool_pre_ping=True)
        self._sessions = sessionmaker(self.engine, expire_on_commit=False)

    def new_session(self) -> Session:
        return self._sessions()

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """A session outside a request (CLI commands, scripts)."""
        session = self.new_session()

        try:
            yield session
        finally:
            session.close()

    def init_app(self, app: Flask) -> None:
        app.extensions["database"] = self

        @app.teardown_appcontext
        def close_session(_error: BaseException | None) -> None:
            session: Session | None = g.pop("db_session", None)

            if session is not None:
                session.close()


def db_session() -> Session:
    """The request's session. Services commit; anything left uncommitted is rolled back."""
    if "db_session" not in g:
        database: Database = current_app.extensions["database"]
        g.db_session = database.new_session()

    session: Session = g.db_session
    return session
