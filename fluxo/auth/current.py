"""Who is calling: resolves the bearer token once per request."""

from flask import g, request

from fluxo.auth.service import AuthService
from fluxo.components import components
from fluxo.database import db_session
from fluxo.errors import UnauthorizedError

BEARER_PREFIX = "Bearer "


def auth_service() -> AuthService:
    parts = components()
    return AuthService(db_session(), parts.clock, parts.settings.token_ttl, parts.login_throttle)


def bearer_token() -> str:
    header = request.headers.get("Authorization", "")

    if not header.startswith(BEARER_PREFIX):
        raise UnauthorizedError("MISSING_TOKEN", "Send 'Authorization: Bearer <token>'.")

    return header.removeprefix(BEARER_PREFIX).strip()


def require_user() -> None:
    """before_request hook for every blueprint that needs a signed-in user."""
    g.user = auth_service().authenticate(bearer_token())


def current_user_id() -> int:
    user_id: int = g.user.id
    return user_id
