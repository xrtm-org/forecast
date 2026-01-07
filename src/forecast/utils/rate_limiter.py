import asyncio
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


LUA_RATE_LIMIT_SCRIPT = """
local tokens_key = KEYS[1]
local timestamp_key = KEYS[2]
local rate = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local last_tokens = tonumber(redis.call("get", tokens_key))
if last_tokens == nil then
    last_tokens = capacity
end

local last_refreshed = tonumber(redis.call("get", timestamp_key))
if last_refreshed == nil then
    last_refreshed = 0
end

local delta = math.max(0, now - last_refreshed)
local filled_tokens = math.min(capacity, last_tokens + (delta * rate))

if filled_tokens >= requested then
    local new_tokens = filled_tokens - requested
    redis.call("set", tokens_key, new_tokens)
    redis.call("set", timestamp_key, now)
    return 1
else
    return 0
end
"""


class TokenBucket:
    """
    Token Bucket Rate Limiter with Redis backend and In-Memory fallback.
    Ensures that we don't exceed a defined rate (requests per minute).
    """

    def __init__(self, redis_url: Optional[str], key: str, rate: float, capacity: float):
        self.redis_url = redis_url
        self.key = key
        self.rate = rate
        self.capacity = capacity
        self.use_redis = False

        # Unconditionally initialize In-Memory state as a fallback
        self._tokens = capacity
        self._last_ts = time.time()
        self._lock = asyncio.Lock()
        self._sync_lock = threading.Lock()

        if redis_url:
            try:
                import redis.asyncio as redis
                self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
                self.script = self.redis.register_script(LUA_RATE_LIMIT_SCRIPT)
                self.use_redis = True
                logger.info(f"[RATE-LIMITER] Using Redis at {redis_url}")
            except ImportError:
                logger.warning("[RATE-LIMITER] Redis not installed, falling back to In-Memory.")
            except Exception as e:
                logger.warning(f"[RATE-LIMITER] Redis connection failed, falling back to In-Memory: {e}")

    async def acquire(self, tokens: int = 1):
        """Blocks until enough tokens are available (Async)."""
        if self.use_redis:
            while True:
                try:
                    now = time.time()
                    allowed = await self.script(
                        keys=[f"{self.key}:tokens", f"{self.key}:ts"],
                        args=[self.rate, self.capacity, now, tokens]
                    )
                    if allowed:
                        return
                except Exception as e:
                    logger.error(f"[RATE-LIMITER] Redis error in acquire: {e}. Switching to In-Memory.")
                    self.use_redis = False
                    break
                await asyncio.sleep(1.0)

        # Fallback to In-Memory logic
        while True:
            async with self._lock:
                now = time.time()
                delta = max(0, now - self._last_ts)
                self._tokens = min(self.capacity, self._tokens + (delta * self.rate))
                self._last_ts = now
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
            await asyncio.sleep(1.0)

    def acquire_sync(self, tokens: int = 1):
        """Blocks until enough tokens are available (Sync)."""
        if self.use_redis:
            import redis as redis_sync
            try:
                r = redis_sync.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
                script = r.register_script(LUA_RATE_LIMIT_SCRIPT)
                while True:
                    now = time.time()
                    if script(keys=[f"{self.key}:tokens", f"{self.key}:ts"], args=[self.rate, self.capacity, now, tokens]):
                        return
                    time.sleep(1.0)
            except Exception as e:
                logger.error(f"[RATE-LIMITER] Redis error in acquire_sync: {e}. Switching to In-Memory.")
                self.use_redis = False

        # Fallback to In-Memory logic (Sync)
        while True:
            with self._sync_lock:
                now = time.time()
                delta = max(0, now - self._last_ts)
                self._tokens = min(self.capacity, self._tokens + (delta * self.rate))
                self._last_ts = now
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
            time.sleep(1.0)
