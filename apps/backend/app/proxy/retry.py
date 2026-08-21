import asyncio
from collections.abc import Awaitable, Callable

import httpx


RETRYABLE_METHODS = {
    "GET",
    "HEAD",
    "OPTIONS",
}

RETRYABLE_STATUS_CODES = {
    502,
    503,
    504,
}


async def retry_request(
    request: Callable[[], Awaitable[httpx.Response]],
    *,
    method: str,
    retries: int = 2,
) -> httpx.Response:
    if method.upper() not in RETRYABLE_METHODS:
        return await request()

    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            response = await request()

            if response.status_code not in RETRYABLE_STATUS_CODES:
                return response

            if attempt >= retries:
                return response

            await response.aclose()

        except (httpx.ConnectError, httpx.ReadTimeout) as exc:
            last_error = exc

            if attempt >= retries:
                raise

        await asyncio.sleep(0.1 * (2**attempt))

    raise RuntimeError("Retry failed") from last_error
