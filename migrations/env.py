"""Alembic runs against DATABASE_URL, or against the connection a caller hands it (the tests do)."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

from fluxo.config import Settings
from fluxo.database import Base
from fluxo.models import *  # noqa: F403 - registers every table on Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


given_connection: Connection | None = config.attributes.get("connection")

if given_connection is not None:
    run_migrations(given_connection)
else:
    engine = create_engine(Settings.from_env().database_url)

    with engine.connect() as connection:
        run_migrations(connection)
