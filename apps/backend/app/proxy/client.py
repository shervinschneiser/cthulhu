from collections.abc import Mapping

import httpx

from app.core.config import settings

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

    async def forward(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        params: Mapping[str, str],
        content: bytes,
    ) -> httpx.Response:
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

        try:
            return await self._client.request(
                method=method,
                url=url,
                headers=filtered_headers,
                params=params,
                content=content,
            )
        except (httpx.ConnectError, httpx.ReadTimeout) as exc:
            raise RuntimeError("Upstream service unavailable") from exc

    async def close(self) -> None:
        await self._client.aclose()
