import asyncio
import time

import pytest

from src.ingestion.rate_limiter import AlphaVantageThrottled, TokenBucket, smart_retry


@pytest.mark.asyncio
async def test_token_bucket_allows_up_to_max_tokens():
    bucket = TokenBucket(max_tokens=3, refill_period=60)

    for _ in range(3):
        await bucket.acquire()

    assert bucket.tokens < 1


@pytest.mark.asyncio
async def test_token_bucket_blocks_when_empty():
    bucket = TokenBucket(max_tokens=2, refill_period=2)

    await bucket.acquire()
    await bucket.acquire()

    start = time.monotonic()
    await bucket.acquire()
    elapsed = time.monotonic() - start

    assert elapsed >= 0.5  # ~2/2 = 1s per token; should wait ~1s


@pytest.mark.asyncio
async def test_smart_retry_succeeds_first_try():
    call_count = 0

    @smart_retry(max_retries=3, base_delay=0.01, bucket=TokenBucket(max_tokens=10, refill_period=1))
    async def succeed():
        nonlocal call_count
        call_count += 1
        return {"data": "ok"}

    result = await succeed()
    assert result == {"data": "ok"}
    assert call_count == 1


@pytest.mark.asyncio
async def test_smart_retry_retries_on_throttle():
    call_count = 0

    @smart_retry(max_retries=3, base_delay=0.01, bucket=TokenBucket(max_tokens=10, refill_period=1))
    async def throttle_then_succeed():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return {"Note": "API rate limit hit"}
        return {"data": "ok"}

    result = await throttle_then_succeed()
    assert result == {"data": "ok"}
    assert call_count == 3


@pytest.mark.asyncio
async def test_smart_retry_raises_after_max_retries():
    @smart_retry(max_retries=2, base_delay=0.01, bucket=TokenBucket(max_tokens=10, refill_period=1))
    async def always_throttle():
        return {"Note": "API rate limit hit"}

    with pytest.raises(AlphaVantageThrottled):
        await always_throttle()


@pytest.mark.asyncio
async def test_smart_retry_retries_on_exception():
    call_count = 0

    @smart_retry(max_retries=3, base_delay=0.01, bucket=TokenBucket(max_tokens=10, refill_period=1))
    async def fail_then_succeed():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("Network error")
        return {"data": "recovered"}

    result = await fail_then_succeed()
    assert result == {"data": "recovered"}
    assert call_count == 2
