"""Integration tests run against a real PostgreSQL, migrated by Alembic exactly like production."""

import os
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from alembic import command
from alembic.config import Config
from flask.testing import FlaskClient
from flask_openapi3 import OpenAPI
from sqlalchemy import Engine, create_engine, text

from fluxo.app import create_app
from fluxo.config import Settings

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://fluxo:fluxo@localhost:5432/fluxo_test"
)
TIMEZONE = ZoneInfo("America/Sao_Paulo")

# Sunday, 15 November 2026, 12:00 in São Paulo.
NOW = datetime(2026, 11, 15, 15, 0, tzinfo=UTC)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TABLES = (
    "budgets",
    "transactions",
    "imports",
    "category_rules",
    "categories",
    "accounts",
    "auth_tokens",
    "users",
)


class MovableClock:
    """A FixedClock tests can move forward, to expire tokens and the like."""

    def __init__(self, instant: datetime) -> None:
        self.instant = instant

    def now(self) -> datetime:
        return self.instant

    def today(self) -> date:
        return self.instant.astimezone(TIMEZONE).date()

    def advance(self, delta: timedelta) -> None:
        self.instant += delta


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    engine = create_engine(TEST_DATABASE_URL)

    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(request: pytest.FixtureRequest) -> None:
    """Every database test starts from empty tables; unit tests never touch the database."""
    if "engine" not in request.fixturenames:
        return

    engine: Engine = request.getfixturevalue("engine")

    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))


@pytest.fixture
def clock() -> MovableClock:
    return MovableClock(NOW)


@pytest.fixture
def settings() -> Settings:
    defaults = Settings.from_env({})
    return replace(defaults, database_url=TEST_DATABASE_URL, timezone=TIMEZONE, demo_enabled=True)


@pytest.fixture
def app(engine: Engine, settings: Settings, clock: MovableClock) -> OpenAPI:
    app = create_app(settings, clock)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app: OpenAPI) -> FlaskClient:
    return app.test_client()


class Api:
    """A signed-in user, so tests read like what the user does, not like HTTP plumbing."""

    def __init__(self, client: FlaskClient, token: str) -> None:
        self.client = client
        self.headers = {"Authorization": f"Bearer {token}"}

    def get(self, url: str, **params: Any) -> Any:
        return self.client.get(url, headers=self.headers, query_string=params)

    def post(self, url: str, json: Any = None, **kwargs: Any) -> Any:
        return self.client.post(url, headers=self.headers, json=json, **kwargs)

    def put(self, url: str, json: Any = None) -> Any:
        return self.client.put(url, headers=self.headers, json=json)

    def patch(self, url: str, json: Any = None) -> Any:
        return self.client.patch(url, headers=self.headers, json=json)

    def delete(self, url: str) -> Any:
        return self.client.delete(url, headers=self.headers)

    def create_account(
        self, name: str = "Checking", kind: str = "checking", opening_balance: str = "0"
    ) -> int:
        response = self.post(
            "/api/accounts", {"name": name, "kind": kind, "opening_balance": opening_balance}
        )
        assert response.status_code == 201, response.json
        account_id: int = response.json["id"]
        return account_id

    def import_csv(self, account_id: int, content: str, invert_amounts: bool = False) -> Any:
        return self.import_file(account_id, content.encode(), "statement.csv", invert_amounts)

    def import_file(
        self, account_id: int, content: bytes, filename: str, invert_amounts: bool = False
    ) -> Any:
        data = {
            "file": (BytesIO(content), filename),
            "account_id": str(account_id),
            "invert_amounts": str(invert_amounts).lower(),
        }
        return self.client.post(
            "/api/imports", headers=self.headers, data=data, content_type="multipart/form-data"
        )

    def category_id(self, name: str) -> int:
        categories = self.get("/api/categories").json["items"]
        return next(category["id"] for category in categories if category["name"] == name)


def sign_up(
    client: FlaskClient, email: str = "ana@example.com", password: str = "correct horse battery"
) -> Api:
    response = client.post("/api/auth/register", json={"name": "Ana", "email": email, "password": password})
    assert response.status_code == 201, response.json
    return Api(client, response.json["token"])


@pytest.fixture
def api(client: FlaskClient) -> Api:
    return sign_up(client)
