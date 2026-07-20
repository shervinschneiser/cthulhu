from collections.abc import Mapping

import httpx


class ProxyClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            timeout=timeout,
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
        return await self._client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            content=content,
        )

    async def close(self) -> None:
        await self._client.aclose()
