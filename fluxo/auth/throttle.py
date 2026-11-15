"""Slows down password guessing: too many failed logins for one e-mail locks it for a while."""

import threading
from collections import deque
from datetime import datetime, timedelta

MAX_FAILURES = 5
WINDOW = timedelta(minutes=15)


class LoginThrottle:
    """Counts failures per e-mail in memory.

    Per process on purpose: no IP addresses are stored anywhere, and a restart
    only gives an attacker five more guesses. With several workers each one
    keeps its own count, which still bounds the guessing rate.
    """

    def __init__(self, max_failures: int = MAX_FAILURES, window: timedelta = WINDOW) -> None:
        self._max_failures = max_failures
        self._window = window
        self._failures: dict[str, deque[datetime]] = {}
        self._lock = threading.Lock()

    def is_locked(self, email: str, now: datetime) -> bool:
        with self._lock:
            recent = self._recent_failures(email, now)
            return len(recent) >= self._max_failures

    def record_failure(self, email: str, now: datetime) -> None:
        with self._lock:
            self._recent_failures(email, now).append(now)

    def reset(self, email: str) -> None:
        with self._lock:
            self._failures.pop(email, None)

    def _recent_failures(self, email: str, now: datetime) -> deque[datetime]:
        failures = self._failures.setdefault(email, deque())

        while failures and now - failures[0] > self._window:
            failures.popleft()

        return failures
