import asyncio

import pytest

from app.gateway.concurrency import ConcurrencyLimiter


async def stream_chunks(
    *chunks: bytes,
    delay: float = 0,
):
    for chunk in chunks:
        if delay:
            await asyncio.sleep(delay)

        yield chunk


@pytest.mark.asyncio
async def test_stream_is_passed_through():
    limiter = ConcurrencyLimiter(limit=2)

    stream = stream_chunks(
        b"hello",
        b"world",
    )

    result = [chunk async for chunk in limiter.limit(stream)]

    assert result == [b"hello", b"world"]


@pytest.mark.asyncio
async def test_concurrency_limit_is_enforced():
    limiter = ConcurrencyLimiter(limit=1)

    first_started = asyncio.Event()
    release_first = asyncio.Event()
    second_started = asyncio.Event()

    async def first_stream():
        first_started.set()
        await release_first.wait()
        yield b"first"

    async def second_stream():
        second_started.set()
        yield b"second"

    async def consume_first():
        return [chunk async for chunk in limiter.limit(first_stream())]

    async def consume_second():
        return [chunk async for chunk in limiter.limit(second_stream())]

    first_task = asyncio.create_task(consume_first())

    await first_started.wait()

    second_task = asyncio.create_task(consume_second())

    await asyncio.sleep(0)

    assert second_started.is_set() is False

    release_first.set()

    assert await first_task == [b"first"]
    assert await second_task == [b"second"]

    assert second_started.is_set() is True


@pytest.mark.asyncio
async def test_slot_is_released_after_stream_finishes():
    limiter = ConcurrencyLimiter(limit=1)

    first = stream_chunks(b"first")
    second = stream_chunks(b"second")

    first_result = [chunk async for chunk in limiter.limit(first)]

    second_result = [chunk async for chunk in limiter.limit(second)]

    assert first_result == [b"first"]
    assert second_result == [b"second"]


@pytest.mark.asyncio
async def test_slot_is_released_when_stream_is_cancelled():
    limiter = ConcurrencyLimiter(limit=1)

    started = asyncio.Event()
    release = asyncio.Event()

    async def blocking_stream():
        started.set()

        try:
            await release.wait()
            yield b"data"
        finally:
            pass

    async def consume():
        async for _ in limiter.limit(blocking_stream()):
            pass

    task = asyncio.create_task(consume())

    await started.wait()

    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    result = [chunk async for chunk in limiter.limit(stream_chunks(b"after-cancel"))]

    assert result == [b"after-cancel"]
