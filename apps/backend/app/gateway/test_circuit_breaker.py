import time

import pytest

from app.gateway.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
)


def test_circuit_starts_closed():
    breaker = CircuitBreaker()

    assert breaker.state is CircuitState.CLOSED
    assert breaker.failures == 0
    assert breaker.allow_request() is True


def test_circuit_opens_after_failure_threshold():
    breaker = CircuitBreaker(failure_threshold=3)

    breaker.record_failure()
    breaker.record_failure()

    assert breaker.state is CircuitState.CLOSED

    breaker.record_failure()

    assert breaker.state is CircuitState.OPEN
    assert breaker.allow_request() is False


def test_circuit_recovers_to_half_open():
    breaker = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout=0.01,
    )

    breaker.record_failure()

    assert breaker.state is CircuitState.OPEN
    assert breaker.allow_request() is False

    time.sleep(0.02)

    assert breaker.allow_request() is True
    assert breaker.state is CircuitState.HALF_OPEN


def test_only_one_half_open_probe_is_allowed():
    breaker = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout=0.01,
    )

    breaker.record_failure()

    time.sleep(0.02)

    assert breaker.allow_request() is True
    assert breaker.allow_request() is False


def test_success_closes_half_open_circuit():
    breaker = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout=0.01,
    )

    breaker.record_failure()

    time.sleep(0.02)

    assert breaker.allow_request() is True
    assert breaker.state is CircuitState.HALF_OPEN

    breaker.record_success()

    assert breaker.state is CircuitState.CLOSED
    assert breaker.failures == 0
    assert breaker.allow_request() is True


def test_failure_reopens_half_open_circuit():
    breaker = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout=0.01,
    )

    breaker.record_failure()

    time.sleep(0.02)

    assert breaker.allow_request() is True
    assert breaker.state is CircuitState.HALF_OPEN

    breaker.record_failure()

    assert breaker.state is CircuitState.OPEN
    assert breaker.allow_request() is False


def test_success_resets_failure_count():
    breaker = CircuitBreaker(failure_threshold=3)

    breaker.record_failure()
    breaker.record_failure()

    assert breaker.failures == 2

    breaker.record_success()

    assert breaker.failures == 0
    assert breaker.state is CircuitState.CLOSED
