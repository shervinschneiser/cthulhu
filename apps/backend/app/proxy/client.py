from collections.abc import Mapping

import httpx

from app.core.config import settings
from app.gateway.circuit_breaker import CircuitBreaker
from app.proxy.exceptions import (
    ProxyTimeoutError,
    UpstreamUnavailableError,
)
from app.proxy.retry import retry_request


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
}


class ProxyClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=settings.proxy_timeout,
            follow_redirects=False,
        )
        self._circuit_breaker = CircuitBreaker()

    async def forward(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        params: Mapping[str, str],
        content: bytes,
    ) -> httpx.Response:
        if not self._circuit_breaker.allow_request():
            raise UpstreamUnavailableError("Circuit breaker is open")

        filtered_headers = {
            key: value
            for key, value in headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS
        }

        filtered_headers.setdefault(
            "user-agent",
            "Cthulhu-Gateway/0.1.0",
        )

        client_ip = headers.get("x-forwarded-for") or headers.get("x-real-ip")

        if client_ip:
            filtered_headers["x-forwarded-for"] = client_ip

        original_host = headers.get("host")

        if original_host:
            filtered_headers["x-forwarded-host"] = original_host

        filtered_headers.setdefault(
            "x-forwarded-proto",
            "http",
        )

        async def send_request() -> httpx.Response:
            return await self._client.request(
                method=method,
                url=url,
                headers=filtered_headers,
                params=params,
                content=content,
            )

        try:
            response = await retry_request(
                send_request,
                method=method,
                retries=2,
            )

            self._circuit_breaker.record_success()

            return response

        except httpx.ConnectError as exc:
            self._circuit_breaker.record_failure()
            raise UpstreamUnavailableError() from exc

        except httpx.ReadTimeout as exc:
            self._circuit_breaker.record_failure()
            raise ProxyTimeoutError() from exc

    async def close(self) -> None:
        await self._client.aclose()
