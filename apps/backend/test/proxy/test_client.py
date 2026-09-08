from unittest.mock import AsyncMock

import httpx
import pytest

from app.gateway.circuit_registry import CircuitBreakerRegistry
from app.proxy.client import ProxyClient
from app.proxy.exceptions import UpstreamUnavailableError


def create_proxy_client() -> ProxyClient:
    return ProxyClient(
        circuit_registry=CircuitBreakerRegistry(),
    )


def test_prepare_headers_removes_hop_by_hop_headers():
    proxy = create_proxy_client()

    headers = {
        "host": "example.com",
        "connection": "keep-alive",
        "transfer-encoding": "chunked",
        "content-type": "application/json",
        "authorization": "Bearer token",
    }

    result = proxy._prepare_headers(headers)

    assert "host" not in result
    assert "connection" not in result
    assert "transfer-encoding" not in result
    assert result["content-type"] == "application/json"
    assert result["authorization"] == "Bearer token"


def test_prepare_headers_sets_default_user_agent():
    proxy = create_proxy_client()

    result = proxy._prepare_headers({})

    assert result["user-agent"] == "Cthulhu-Gateway/0.1.0"


def test_prepare_headers_forwards_client_ip():
    proxy = create_proxy_client()

    result = proxy._prepare_headers(
        {
            "x-forwarded-for": "192.168.1.10",
        }
    )

    assert result["x-forwarded-for"] == "192.168.1.10"


def test_prepare_headers_forwards_original_host():
    proxy = create_proxy_client()

    result = proxy._prepare_headers(
        {
            "host": "api.example.com",
        }
    )

    assert result["x-forwarded-host"] == "api.example.com"


def test_prepare_headers_sets_forwarded_proto():
    proxy = create_proxy_client()

    result = proxy._prepare_headers({})

    assert result["x-forwarded-proto"] == "http"


def test_get_circuit_breaker_uses_origin():
    registry = CircuitBreakerRegistry()
    proxy = ProxyClient(
        circuit_registry=registry,
    )

    first = proxy._get_circuit_breaker(
        "http://localhost:9000/users?page=1",
    )

    second = proxy._get_circuit_breaker(
        "http://localhost:9000/orders",
    )

    assert first is second


def test_invalid_upstream_url_raises_value_error():
    proxy = create_proxy_client()

    with pytest.raises(
        ValueError,
        match="Invalid upstream URL",
    ):
        proxy._get_circuit_breaker(
            "localhost:9000/users",
        )


@pytest.mark.asyncio
async def test_forward_rejects_open_circuit():
    registry = CircuitBreakerRegistry()

    proxy = ProxyClient(
        circuit_registry=registry,
    )

    breaker = registry.get("http://localhost:9000")

    for _ in range(breaker.failure_threshold):
        breaker.record_failure()

    with pytest.raises(UpstreamUnavailableError):
        await proxy.forward(
            method="GET",
            url="http://localhost:9000/users",
            headers={},
            params={},
            content=b"",
        )


@pytest.mark.asyncio
async def test_forward_returns_upstream_response():
    registry = CircuitBreakerRegistry()

    proxy = ProxyClient(
        circuit_registry=registry,
    )

    response = httpx.Response(
        200,
        content=b'{"ok": true}',
    )

    proxy._client.request = AsyncMock(
        return_value=response,
    )

    result = await proxy.forward(
        method="GET",
        url="http://localhost:9000/users",
        headers={},
        params={},
        content=b"",
    )

    assert result.status_code == 200
    assert result.content == b'{"ok": true}'

    proxy._client.request.assert_awaited_once()

    await proxy.close()
