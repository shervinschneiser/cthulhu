from unittest.mock import AsyncMock

import httpx
import pytest

from app.gateway.circuit_registry import CircuitBreakerRegistry
from app.proxy.client import ProxyClient
from app.proxy.exceptions import ProxyTimeoutError


@pytest.mark.asyncio
async def test_stream_returns_upstream_response_and_body():
    registry = CircuitBreakerRegistry()

    proxy = ProxyClient(
        circuit_registry=registry,
    )

    response = httpx.Response(
        200,
        content=b"hello world",
    )

    proxy._client.send = AsyncMock(
        return_value=response,
    )

    result, stream = await proxy.stream(
        method="GET",
        url="http://localhost:9000/users",
        headers={},
        params={},
        content=iter(()),
    )

    chunks = [chunk async for chunk in stream]

    assert result.status_code == 200
    assert b"".join(chunks) == b"hello world"

    breaker = registry.get("http://localhost:9000")

    assert breaker.failures == 0

    await proxy.close()


@pytest.mark.asyncio
async def test_stream_records_success_after_body_is_consumed():
    registry = CircuitBreakerRegistry()

    proxy = ProxyClient(
        circuit_registry=registry,
    )

    response = httpx.Response(
        200,
        content=b"data",
    )

    proxy._client.send = AsyncMock(
        return_value=response,
    )

    _, stream = await proxy.stream(
        method="GET",
        url="http://localhost:9000/users",
        headers={},
        params={},
        content=iter(()),
    )

    breaker = registry.get("http://localhost:9000")

    breaker.record_failure()

    assert breaker.failures == 1

    chunks = [chunk async for chunk in stream]

    assert b"".join(chunks) == b"data"
    assert breaker.failures == 0


@pytest.mark.asyncio
async def test_stream_records_failure_on_read_timeout():
    registry = CircuitBreakerRegistry()

    proxy = ProxyClient(
        circuit_registry=registry,
    )

    response = httpx.Response(
        200,
        content=b"data",
    )

    response.aiter_bytes = lambda: failing_stream()

    proxy._client.send = AsyncMock(
        return_value=response,
    )

    _, stream = await proxy.stream(
        method="GET",
        url="http://localhost:9000/users",
        headers={},
        params={},
        content=iter(()),
    )

    async def consume():
        async for _ in stream:
            pass

    with pytest.raises(ProxyTimeoutError):
        await consume()

    breaker = registry.get("http://localhost:9000")

    assert breaker.failures == 1

    await proxy.close()


async def failing_stream():
    yield b"partial"

    raise httpx.ReadTimeout("stream read timeout")


@pytest.mark.asyncio
async def test_stream_rejects_open_circuit():
    registry = CircuitBreakerRegistry()

    proxy = ProxyClient(
        circuit_registry=registry,
    )

    breaker = registry.get("http://localhost:9000")

    for _ in range(breaker.failure_threshold):
        breaker.record_failure()

    with pytest.raises(Exception):
        await proxy.stream(
            method="GET",
            url="http://localhost:9000/users",
            headers={},
            params={},
            content=iter(()),
        )

    await proxy.close()
