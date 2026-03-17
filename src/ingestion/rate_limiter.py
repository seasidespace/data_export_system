import asyncio
import functools
import logging
import time
from typing import Any, Callable

from src.config import settings

logger = logging.getLogger(__name__)

THROTTLE_SENTINEL = "Note"


class TokenBucket:
    """Token-bucket rate limiter for Alpha Vantage's free-tier cap."""

    def __init__(self, max_tokens: int | None = None, refill_period: float | None = None):
        self.max_tokens = max_tokens or settings.rate_limit_calls
        self.refill_period = refill_period or settings.rate_limit_period
        self.tokens = float(self.max_tokens)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        new_tokens = elapsed * (self.max_tokens / self.refill_period)
        self.tokens = min(self.max_tokens, self.tokens + new_tokens)
        self._last_refill = now

    async def acquire(self) -> None:
        async with self._lock:
            self._refill()
            while self.tokens < 1:
                wait = (1 - self.tokens) * (self.refill_period / self.max_tokens)
                logger.info("Rate limit reached — waiting %.1fs for next token", wait)
                await asyncio.sleep(wait)
                self._refill()
            self.tokens -= 1


_default_bucket = TokenBucket()


class AlphaVantageThrottled(Exception):
    """Raised when the API returns its throttle 'Note' instead of real data."""


def smart_retry(
    max_retries: int = 4,
    base_delay: float = 2.0,
    bucket: TokenBucket | None = None,
) -> Callable:
    """Decorator that respects the token bucket and retries on transient failures.

    Handles both HTTP-level errors (429, 5xx) and Alpha Vantage's in-body
    throttle signal (a top-level "Note" key in the JSON response).
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            _bucket = bucket or _default_bucket

            for attempt in range(1, max_retries + 1):
                await _bucket.acquire()
                try:
                    result = await fn(*args, **kwargs)

                    if isinstance(result, dict) and THROTTLE_SENTINEL in result:
                        raise AlphaVantageThrottled(result[THROTTLE_SENTINEL])

                    return result

                except AlphaVantageThrottled as exc:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Throttled by Alpha Vantage (attempt %d/%d): %s — retrying in %.1fs",
                        attempt,
                        max_retries,
                        exc,
                        delay,
                    )
                    if attempt == max_retries:
                        raise
                    await asyncio.sleep(delay)

                except Exception as exc:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.error(
                        "Request failed (attempt %d/%d): %s — retrying in %.1fs",
                        attempt,
                        max_retries,
                        exc,
                        delay,
                    )
                    if attempt == max_retries:
                        raise
                    await asyncio.sleep(delay)

            raise RuntimeError("Exhausted retries — this should be unreachable")

        return wrapper

    return decorator
