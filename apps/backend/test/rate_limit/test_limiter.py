import pytest

from app.rate_limit.limiter import RateLimiter


class FakeRedis:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, seconds: int) -> bool:
        return True


@pytest.mark.asyncio
async def test_allows_requests_under_limit():
    redis = FakeRedis()
    limiter = RateLimiter(redis, limit=3)

    assert await limiter.allow("client-1") is True
    assert await limiter.allow("client-1") is True
    assert await limiter.allow("client-1") is True


@pytest.mark.asyncio
async def test_rejects_requests_over_limit():
    redis = FakeRedis()
    limiter = RateLimiter(redis, limit=2)

    assert await limiter.allow("client-1") is True
    assert await limiter.allow("client-1") is True
    assert await limiter.allow("client-1") is False


@pytest.mark.asyncio
async def test_different_keys_have_independent_limits():
    redis = FakeRedis()
    limiter = RateLimiter(redis, limit=1)

    assert await limiter.allow("client-1") is True
    assert await limiter.allow("client-1") is False

    assert await limiter.allow("client-2") is True
