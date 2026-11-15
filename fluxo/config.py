"""Application settings, read once from the environment."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo

DEFAULT_DATABASE_URL = "postgresql+psycopg://fluxo:fluxo@localhost:5432/fluxo"
DEFAULT_TIMEZONE = "America/Sao_Paulo"
DEFAULT_TOKEN_TTL_DAYS = 30
DEFAULT_MAX_UPLOAD_KB = 2048


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    timezone: ZoneInfo
    token_ttl: timedelta
    max_upload_bytes: int
    demo_enabled: bool

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        return cls(
            database_url=env.get("DATABASE_URL", DEFAULT_DATABASE_URL),
            timezone=ZoneInfo(env.get("APP_TIMEZONE", DEFAULT_TIMEZONE)),
            token_ttl=timedelta(days=int(env.get("TOKEN_TTL_DAYS", DEFAULT_TOKEN_TTL_DAYS))),
            max_upload_bytes=int(env.get("MAX_UPLOAD_KB", DEFAULT_MAX_UPLOAD_KB)) * 1024,
            demo_enabled=env.get("DEMO_ENABLED", "false").lower() == "true",
        )
