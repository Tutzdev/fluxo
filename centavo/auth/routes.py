from flask import g
from flask_openapi3 import APIBlueprint, Tag

from centavo.auth.current import auth_service, bearer_token, require_user
from centavo.auth.models import User
from centavo.auth.schemas import LoginRequest, RegisterRequest, SessionResponse, UserResponse
from centavo.auth.service import IssuedToken
from centavo.openapi import BEARER_SECURITY

tag = Tag(name="Auth", description="Create an account and get a bearer token")

public = APIBlueprint("auth", __name__, url_prefix="/api/auth", abp_tags=[tag])
private = APIBlueprint("me", __name__, url_prefix="/api/auth", abp_tags=[tag], abp_security=BEARER_SECURITY)
private.before_request(require_user)


@public.post("/register", responses={201: SessionResponse})
def register(body: RegisterRequest) -> tuple[dict[str, object], int]:
    issued = auth_service().register(body.name, body.email, body.password)
    return _session_json(issued), 201


@public.post("/login", responses={200: SessionResponse})
def login(body: LoginRequest) -> dict[str, object]:
    issued = auth_service().login(body.email, body.password)
    return _session_json(issued)


@private.post("/logout", responses={204: None})
def logout() -> tuple[str, int]:
    auth_service().logout(bearer_token())
    return "", 204


@private.get("/me", responses={200: UserResponse})
def me() -> dict[str, object]:
    return _user_response(g.user).model_dump(mode="json")


def _session_json(issued: IssuedToken) -> dict[str, object]:
    response = SessionResponse(
        token=issued.token, expires_at=issued.expires_at, user=_user_response(issued.user)
    )
    return response.model_dump(mode="json")


def _user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, name=user.name, email=user.email)
