from collections.abc import Awaitable, Callable

import httpx

RETRYABLE_METHODS = {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}


async def retry_request(
    request: Callable[[], Awaitable[httpx.Response]],
    *,
    method: str,
    retries: int = 2,
) -> httpx.Response:
    attempts = 0

    while True:
        try:
            return await request()
        except (httpx.ConnectError, httpx.ReadTimeout):
            if method.upper() not in RETRYABLE_METHODS or attempts >= retries:
                raise

            attempts += 1
