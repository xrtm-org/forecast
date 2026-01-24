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

r"""Unit tests for ResilientProvider."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from xrtm.forecast.core.resilience import ResilientProvider
from xrtm.forecast.core.resilience.wrapper import RetryConfig


class TestRetryConfig:
    r"""Test RetryConfig."""

    def test_default_values(self):
        r"""Default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_wait == 1.0
        assert config.max_wait == 60.0
        assert config.jitter is True

    def test_calculate_wait_no_jitter(self):
        r"""Wait time calculation without jitter."""
        config = RetryConfig(initial_wait=1.0, exponential_base=2.0, jitter=False)
        assert config.calculate_wait(0) == 1.0
        assert config.calculate_wait(1) == 2.0
        assert config.calculate_wait(2) == 4.0

    def test_calculate_wait_respects_max(self):
        r"""Wait time respects max_wait."""
        config = RetryConfig(initial_wait=10.0, max_wait=15.0, jitter=False)
        assert config.calculate_wait(0) == 10.0
        assert config.calculate_wait(1) == 15.0  # Capped at max
        assert config.calculate_wait(2) == 15.0  # Still capped


class TestResilientProviderBasics:
    r"""Test ResilientProvider basic operations."""

    def test_delegates_attributes(self):
        r"""Provider attributes are delegated."""
        mock_provider = MagicMock()
        mock_provider.model_id = "gemini-pro"
        resilient = ResilientProvider(mock_provider)
        assert resilient.model_id == "gemini-pro"

    def test_config_override(self):
        r"""Config can be overridden via max_retries param."""
        resilient = ResilientProvider(None, max_retries=10)
        assert resilient.config.max_retries == 10

    def test_stats_initial(self):
        r"""Stats are zero initially."""
        resilient = ResilientProvider(None)
        stats = resilient.stats()
        assert stats["total_calls"] == 0
        assert stats["total_retries"] == 0
        assert stats["retry_rate"] == 0.0


class TestResilientProviderAsync:
    r"""Test async retry logic."""

    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self):
        r"""Successful call does not trigger retry."""

        async def success_func():
            return "ok"

        resilient = ResilientProvider(None)
        result = await resilient.execute_with_retry(success_func)
        assert result == "ok"
        assert resilient.stats()["total_retries"] == 0

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        r"""ConnectionError triggers retry."""
        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network failed")
            return "success"

        config = RetryConfig(max_retries=3, initial_wait=0.01, jitter=False)
        resilient = ResilientProvider(None, config=config)
        result = await resilient.execute_with_retry(flaky_func)

        assert result == "success"
        assert call_count == 3
        assert resilient.stats()["total_retries"] == 2

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises(self):
        r"""All retries exhausted raises exception."""

        async def always_fail():
            raise ConnectionError("Always fails")

        config = RetryConfig(max_retries=2, initial_wait=0.01, jitter=False)
        resilient = ResilientProvider(None, config=config)

        with pytest.raises(ConnectionError):
            await resilient.execute_with_retry(always_fail)

        assert resilient.stats()["total_retries"] == 2

    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        r"""on_retry callback is called."""
        retry_log = []

        def log_retry(attempt, exc, wait):
            retry_log.append((attempt, str(exc), wait))

        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Slow")
            return "done"

        config = RetryConfig(max_retries=3, initial_wait=0.01, jitter=False)
        resilient = ResilientProvider(None, config=config, on_retry=log_retry)
        await resilient.execute_with_retry(flaky_func)

        assert len(retry_log) == 1
        assert retry_log[0][0] == 0  # First attempt
        assert "Slow" in retry_log[0][1]


class TestResilientProviderSync:
    r"""Test sync retry logic."""

    def test_sync_successful_call(self):
        r"""Sync successful call works."""

        def success_func():
            return "sync_ok"

        resilient = ResilientProvider(None)
        result = resilient.execute_sync_with_retry(success_func)
        assert result == "sync_ok"

    def test_sync_retry_on_error(self):
        r"""Sync retry on error."""
        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OSError("Disk error")
            return "recovered"

        config = RetryConfig(max_retries=3, initial_wait=0.01, jitter=False)
        resilient = ResilientProvider(None, config=config)
        result = resilient.execute_sync_with_retry(flaky_func)

        assert result == "recovered"
        assert call_count == 2
