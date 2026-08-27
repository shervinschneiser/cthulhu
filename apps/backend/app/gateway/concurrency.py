import asyncio
from collections.abc import AsyncIterator


class ConcurrencyLimiter:
    def __init__(
        self,
        limit: int = 100,
    ) -> None:
        self._semaphore = asyncio.Semaphore(limit)

    async def acquire(self) -> None:
        await self._semaphore.acquire()

    def release(self) -> None:
        self._semaphore.release()

    async def limit(
        self,
        stream: AsyncIterator[bytes],
    ) -> AsyncIterator[bytes]:
        await self.acquire()

        try:
            async for chunk in stream:
                yield chunk
        finally:
            self.release()
