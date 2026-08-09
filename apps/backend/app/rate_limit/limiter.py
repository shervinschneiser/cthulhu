from redis.asyncio import Redis


class RateLimiter:
    def __init__(self, redis: Redis, limit: int = 100) -> None:
        self._redis = redis
        self._limit = limit

    async def allow(self, key: str) -> bool:
        count = await self._redis.incr(key)

        if count == 1:
            await self._redis.expire(key, 60)

        return count <= self._limit
