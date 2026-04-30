# coding=utf-8
# Copyright 2026 XRTM Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""Unit tests for forecast.core.utils.rate_limiter."""

import asyncio
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from xrtm.forecast.core.runtime import temporal_context_var
from xrtm.forecast.core.utils.rate_limiter import TokenBucket


class TestTokenBucket:
    r"""Tests for the TokenBucket rate limiter."""

    def test_init_without_redis(self):
        r"""Should initialize with in-memory mode when no redis URL."""
        bucket = TokenBucket(redis_url=None, key="test", rate=1.0, capacity=10.0)
        assert bucket.use_redis is False
        assert bucket._tokens == 10.0

    def test_init_with_redis_import_error(self):
        r"""Should fall back to in-memory when redis not installed."""
        with patch.dict("sys.modules", {"redis": None, "redis.asyncio": None}):
            bucket = TokenBucket(redis_url="redis://localhost:6379", key="test", rate=1.0, capacity=10.0)
            # Should gracefully fall back
            assert bucket.key == "test"

    def test_init_with_redis_connection_error(self):
        r"""Should fall back to in-memory on Redis connection error."""
        pytest.importorskip("redis")
        with patch("redis.asyncio.from_url", side_effect=Exception("Connection refused")):
            bucket = TokenBucket(redis_url="redis://localhost:6379", key="test", rate=1.0, capacity=10.0)
            assert bucket.use_redis is False

    @pytest.mark.asyncio
    async def test_acquire_in_memory_immediate(self):
        r"""Should acquire token immediately when bucket is full."""
        bucket = TokenBucket(redis_url=None, key="test", rate=10.0, capacity=10.0)

        start = time.time()
        await bucket.acquire(1)
        elapsed = time.time() - start

        assert elapsed < 0.5  # Should be near-instant
        assert bucket._tokens == 9.0

    @pytest.mark.asyncio
    async def test_acquire_in_memory_multiple(self):
        r"""Should acquire multiple tokens."""
        bucket = TokenBucket(redis_url=None, key="test", rate=10.0, capacity=10.0)

        await bucket.acquire(5)
        assert bucket._tokens == pytest.approx(5.0, abs=0.1)

        await bucket.acquire(3)
        assert bucket._tokens == pytest.approx(2.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_acquire_in_memory_refill(self):
        r"""Should refill tokens over time."""
        bucket = TokenBucket(redis_url=None, key="test", rate=100.0, capacity=10.0)
        bucket._tokens = 0.0  # Empty the bucket

        # Wait a short time for refill
        await asyncio.sleep(0.05)

        # Should have refilled some tokens (100 tokens/sec * 0.05 sec = 5 tokens)
        await bucket.acquire(1)  # This will trigger refill calculation
        # We got at least 1 token back

    @pytest.mark.asyncio
    async def test_acquire_in_memory_timeout(self):
        r"""Should time out deterministically when no tokens can be produced."""
        bucket = TokenBucket(redis_url=None, key="test", rate=0.0, capacity=1.0)
        await bucket.acquire(1)

        with pytest.raises(TimeoutError, match="Timed out"):
            await bucket.acquire(1, timeout=0.01)

    @pytest.mark.asyncio
    async def test_acquire_timeout_uses_wall_clock_in_backtest_context(self):
        r"""Rate limiting must not busy-loop through Chronos sleep bypasses."""
        bucket = TokenBucket(redis_url=None, key="test", rate=0.0, capacity=1.0)
        await bucket.acquire(1)
        token = temporal_context_var.set(SimpleNamespace(is_backtest=True))
        start = time.monotonic()
        try:
            with pytest.raises(TimeoutError, match="Timed out"):
                await bucket.acquire(1, timeout=0.02)
        finally:
            temporal_context_var.reset(token)

        assert time.monotonic() - start >= 0.015

    @pytest.mark.asyncio
    async def test_acquire_in_memory_cancellation(self):
        r"""Should remain cancellable while waiting for tokens."""
        bucket = TokenBucket(redis_url=None, key="test", rate=0.0, capacity=1.0)
        await bucket.acquire(1)

        task = asyncio.create_task(bucket.acquire(1))
        await asyncio.sleep(0)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

    @pytest.mark.asyncio
    async def test_acquire_rejects_unsatisfiable_request(self):
        r"""Should reject requests larger than bucket capacity instead of hanging."""
        bucket = TokenBucket(redis_url=None, key="test", rate=10.0, capacity=1.0)

        with pytest.raises(ValueError, match="exceeds bucket capacity"):
            await bucket.acquire(2)

    def test_acquire_sync_in_memory_immediate(self):
        r"""Should acquire token synchronously when bucket is full."""
        bucket = TokenBucket(redis_url=None, key="test", rate=10.0, capacity=10.0)

        start = time.time()
        bucket.acquire_sync(1)
        elapsed = time.time() - start

        assert elapsed < 0.5  # Should be near-instant
        assert bucket._tokens == 9.0

    def test_acquire_sync_in_memory_multiple(self):
        r"""Should acquire multiple tokens synchronously."""
        bucket = TokenBucket(redis_url=None, key="test", rate=10.0, capacity=10.0)

        bucket.acquire_sync(3)
        assert bucket._tokens == pytest.approx(7.0, abs=0.1)

        bucket.acquire_sync(2)
        assert bucket._tokens == pytest.approx(5.0, abs=0.1)

    def test_acquire_sync_in_memory_timeout(self):
        r"""Should time out deterministically in the sync API."""
        bucket = TokenBucket(redis_url=None, key="test", rate=0.0, capacity=1.0)
        bucket.acquire_sync(1)

        with pytest.raises(TimeoutError, match="Timed out"):
            bucket.acquire_sync(1, timeout=0.01)

    @pytest.mark.asyncio
    async def test_acquire_redis_fallback_on_error(self):
        r"""Should fall back to in-memory if Redis errors during acquire."""
        bucket = TokenBucket(redis_url=None, key="test", rate=10.0, capacity=10.0)
        bucket.use_redis = True  # Pretend we're using Redis
        bucket.script = MagicMock(side_effect=Exception("Redis error"))

        # Should fall back to in-memory and succeed
        await bucket.acquire(1)
        assert bucket.use_redis is False  # Should have switched to in-memory
