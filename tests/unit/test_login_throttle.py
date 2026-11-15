from datetime import UTC, datetime, timedelta

from fluxo.auth.throttle import LoginThrottle

NOW = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)


def test_locks_after_too_many_failures_in_the_window():
    throttle = LoginThrottle(max_failures=3, window=timedelta(minutes=15))

    for _ in range(3):
        throttle.record_failure("ana@example.com", NOW)

    assert throttle.is_locked("ana@example.com", NOW)
    assert not throttle.is_locked("bia@example.com", NOW)


def test_old_failures_stop_counting():
    throttle = LoginThrottle(max_failures=2, window=timedelta(minutes=15))
    throttle.record_failure("ana@example.com", NOW)
    throttle.record_failure("ana@example.com", NOW)

    assert not throttle.is_locked("ana@example.com", NOW + timedelta(minutes=16))


def test_a_successful_login_clears_the_count():
    throttle = LoginThrottle(max_failures=2, window=timedelta(minutes=15))
    throttle.record_failure("ana@example.com", NOW)
    throttle.record_failure("ana@example.com", NOW)

    throttle.reset("ana@example.com")

    assert not throttle.is_locked("ana@example.com", NOW)
