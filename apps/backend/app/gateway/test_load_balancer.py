import pytest

from app.gateway.circuit_registry import CircuitBreakerRegistry
from app.gateway.load_balancer import LoadBalancer


def create_load_balancer() -> LoadBalancer:
    registry = CircuitBreakerRegistry()

    return LoadBalancer(
        upstreams=[
            "http://localhost:9000",
            "http://localhost:9001",
            "http://localhost:9002",
        ],
        circuit_registry=registry,
    )


def test_round_robin_distribution():
    load_balancer = create_load_balancer()

    assert load_balancer.next() == "http://localhost:9000"
    assert load_balancer.next() == "http://localhost:9001"
    assert load_balancer.next() == "http://localhost:9002"
    assert load_balancer.next() == "http://localhost:9000"


def test_skips_open_upstream():
    load_balancer = create_load_balancer()

    breaker = load_balancer.circuit_registry.get(
        "http://localhost:9001",
    )

    for _ in range(breaker.failure_threshold):
        breaker.record_failure()

    assert breaker.is_open() is True

    assert load_balancer.next() == "http://localhost:9000"
    assert load_balancer.next() == "http://localhost:9002"
    assert load_balancer.next() == "http://localhost:9000"


def test_raises_when_all_upstreams_are_open():
    load_balancer = create_load_balancer()

    for upstream in load_balancer.upstreams:
        breaker = load_balancer.circuit_registry.get(upstream)

        for _ in range(breaker.failure_threshold):
            breaker.record_failure()

    with pytest.raises(
        RuntimeError,
        match="No healthy upstream available",
    ):
        load_balancer.next()


def test_empty_upstreams_raise_value_error():
    registry = CircuitBreakerRegistry()

    load_balancer = LoadBalancer(
        upstreams=[],
        circuit_registry=registry,
    )

    with pytest.raises(
        ValueError,
        match="No upstreams configured",
    ):
        load_balancer.next()
