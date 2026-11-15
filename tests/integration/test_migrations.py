from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from centavo.database import Base
from centavo.models import *  # noqa: F403 - every table on Base.metadata


def test_the_migrations_create_exactly_what_the_models_describe(engine):
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        differences = compare_metadata(context, Base.metadata)

    assert differences == []
