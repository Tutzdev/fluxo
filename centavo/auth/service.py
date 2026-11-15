"""Sign up, sign in, sign out, and turning a bearer token back into a user."""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from centavo.auth.models import AuthToken, User
from centavo.auth.throttle import LoginThrottle
from centavo.categories.defaults import create_starter_kit
from centavo.clock import Clock
from centavo.errors import ConflictError, TooManyRequestsError, UnauthorizedError

# Checked when the e-mail does not exist, so a wrong e-mail takes as long as a wrong password.
_DUMMY_PASSWORD_HASH = generate_password_hash("never-a-real-password")


@dataclass(frozen=True, slots=True)
class IssuedToken:
    token: str
    expires_at: datetime
    user: User


class AuthService:
    def __init__(self, session: Session, clock: Clock, token_ttl: timedelta, throttle: LoginThrottle) -> None:
        self._session = session
        self._clock = clock
        self._token_ttl = token_ttl
        self._throttle = throttle

    def register(self, name: str, email: str, password: str) -> IssuedToken:
        user = User(name=name, email=email.lower(), password_hash=generate_password_hash(password))
        self._session.add(user)

        try:
            self._session.flush()
        except IntegrityError as error:
            # The unique index decides, so two sign-ups racing for one e-mail cannot both win.
            self._session.rollback()
            raise ConflictError("EMAIL_TAKEN", "There is already an account with this e-mail.") from error

        create_starter_kit(self._session, user.id)
        issued = self._issue_token(user)

        self._session.commit()
        return issued

    def login(self, email: str, password: str) -> IssuedToken:
        now = self._clock.now()
        throttle_key = email.lower()

        if self._throttle.is_locked(throttle_key, now):
            raise TooManyRequestsError(
                "TOO_MANY_ATTEMPTS", "Too many failed attempts. Try again in a few minutes."
            )

        user = self._find_by_email(email)
        password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
        password_matches = check_password_hash(password_hash, password)

        if user is None or not password_matches:
            self._throttle.record_failure(throttle_key, now)
            raise UnauthorizedError("INVALID_CREDENTIALS", "E-mail or password is incorrect.")

        self._throttle.reset(throttle_key)
        self._delete_expired_tokens(user.id, now)
        issued = self._issue_token(user)

        self._session.commit()
        return issued

    def authenticate(self, raw_token: str) -> User:
        token = self._session.scalars(
            select(AuthToken).where(AuthToken.token_hash == _hash_token(raw_token))
        ).one_or_none()

        if token is None or token.expires_at <= self._clock.now():
            raise UnauthorizedError("INVALID_TOKEN", "Sign in again.")

        return self._session.get_one(User, token.user_id)

    def logout(self, raw_token: str) -> None:
        self._session.execute(delete(AuthToken).where(AuthToken.token_hash == _hash_token(raw_token)))
        self._session.commit()

    def _find_by_email(self, email: str) -> User | None:
        statement = select(User).where(func.lower(User.email) == email.lower())
        return self._session.scalars(statement).one_or_none()

    def _issue_token(self, user: User) -> IssuedToken:
        raw_token = secrets.token_urlsafe(32)
        expires_at = self._clock.now() + self._token_ttl

        self._session.add(
            AuthToken(user_id=user.id, token_hash=_hash_token(raw_token), expires_at=expires_at)
        )
        return IssuedToken(token=raw_token, expires_at=expires_at, user=user)

    def _delete_expired_tokens(self, user_id: int, now: datetime) -> None:
        self._session.execute(
            delete(AuthToken).where(AuthToken.user_id == user_id, AuthToken.expires_at <= now)
        )


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()
