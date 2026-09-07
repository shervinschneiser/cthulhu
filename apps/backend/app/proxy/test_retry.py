from unittest.mock import AsyncMock

import httpx
import pytest

from app.proxy.retry import retry_request


@pytest.mark.asyncio
async def test_successful_request_is_not_retried():
    response = httpx.Response(200)

    request = AsyncMock(return_value=response)

    result = await retry_request(
        request,
        method="GET",
        retries=2,
    )

    assert result is response
    assert request.await_count == 1


@pytest.mark.asyncio
async def test_get_is_retried_after_connect_error():
    response = httpx.Response(200)

    request = AsyncMock(
        side_effect=[
            httpx.ConnectError("connection failed"),
            response,
        ],
    )

    result = await retry_request(
        request,
        method="GET",
        retries=2,
    )

    assert result is response
    assert request.await_count == 2


@pytest.mark.asyncio
async def test_get_is_retried_after_read_timeout():
    response = httpx.Response(200)

    request = AsyncMock(
        side_effect=[
            httpx.ReadTimeout("read timeout"),
            response,
        ],
    )

    result = await retry_request(
        request,
        method="GET",
        retries=2,
    )

    assert result is response
    assert request.await_count == 2


@pytest.mark.asyncio
async def test_retry_stops_after_max_retries():
    request = AsyncMock(
        side_effect=httpx.ConnectError("connection failed"),
    )

    with pytest.raises(httpx.ConnectError):
        await retry_request(
            request,
            method="GET",
            retries=2,
        )

    assert request.await_count == 3


@pytest.mark.asyncio
async def test_post_is_not_retried():
    request = AsyncMock(
        side_effect=httpx.ConnectError("connection failed"),
    )

    with pytest.raises(httpx.ConnectError):
        await retry_request(
            request,
            method="POST",
            retries=2,
        )

    assert request.await_count == 1


@pytest.mark.asyncio
async def test_put_is_not_retried():
    request = AsyncMock(
        side_effect=httpx.ConnectError("connection failed"),
    )

    with pytest.raises(httpx.ConnectError):
        await retry_request(
            request,
            method="PUT",
            retries=2,
        )

    assert request.await_count == 1


@pytest.mark.asyncio
async def test_delete_is_not_retried():
    request = AsyncMock(
        side_effect=httpx.ConnectError("connection failed"),
    )

    with pytest.raises(httpx.ConnectError):
        await retry_request(
            request,
            method="DELETE",
            retries=2,
        )

    assert request.await_count == 1
