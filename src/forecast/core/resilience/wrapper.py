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

r"""Resilient provider wrapper with retry logic and telemetry integration.

This module provides a wrapper that adds production-grade retry logic to any
InferenceProvider, including jittered exponential backoff and error discrimination.

Example:
    >>> from forecast.core.resilience import ResilientProvider
    >>> from forecast.providers.inference import GeminiProvider
    >>> base_provider = GeminiProvider(model_id="gemini-pro")
    >>> resilient = ResilientProvider(base_provider, max_retries=3)
    >>> # Now use resilient instead of base_provider
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any, Callable, Optional, TypeVar

__all__ = ["ResilientProvider", "RetryConfig"]

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    r"""Configuration for retry behavior.

    Args:
        max_retries (`int`, *optional*, defaults to `3`):
            Maximum number of retry attempts.
        initial_wait (`float`, *optional*, defaults to `1.0`):
            Initial wait time in seconds before first retry.
        max_wait (`float`, *optional*, defaults to `60.0`):
            Maximum wait time in seconds between retries.
        exponential_base (`float`, *optional*, defaults to `2.0`):
            Base for exponential backoff calculation.
        jitter (`bool`, *optional*, defaults to `True`):
            Whether to add random jitter to wait times.
        retryable_exceptions (`tuple`, *optional*):
            Exception types that should trigger a retry.

    Example:
        >>> config = RetryConfig(max_retries=5, initial_wait=0.5)
        >>> config.max_retries
        5
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_wait: float = 1.0,
        max_wait: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[tuple] = None,
    ) -> None:
        self.max_retries = max_retries
        self.initial_wait = initial_wait
        self.max_wait = max_wait
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (
            ConnectionError,
            TimeoutError,
            OSError,
        )

    def calculate_wait(self, attempt: int) -> float:
        r"""Calculate wait time for a given attempt number.

        Args:
            attempt (`int`):
                The current attempt number (0-indexed).

        Returns:
            `float`: Wait time in seconds.

        Example:
            >>> config = RetryConfig(initial_wait=1.0, jitter=False)
            >>> config.calculate_wait(0)
            1.0
            >>> config.calculate_wait(1)
            2.0
        """
        wait = min(
            self.initial_wait * (self.exponential_base**attempt),
            self.max_wait,
        )
        if self.jitter:
            wait = wait * (0.5 + random.random())
        return wait


class ResilientProvider:
    r"""Wrapper that adds retry logic to any provider.

    This wrapper intercepts calls and adds production-grade retry behavior
    with jittered exponential backoff and error discrimination.

    Args:
        provider (`Any`):
            The underlying provider to wrap.
        config (`RetryConfig`, *optional*):
            Retry configuration. If not provided, uses defaults.
        max_retries (`int`, *optional*, defaults to `3`):
            Shortcut for setting max_retries in config.
        on_retry (`Callable`, *optional*):
            Callback function called on each retry with (attempt, exception, wait_time).

    Example:
        >>> from unittest.mock import MagicMock
        >>> mock_provider = MagicMock()
        >>> resilient = ResilientProvider(mock_provider, max_retries=5)
        >>> resilient.config.max_retries
        5
    """

    def __init__(
        self,
        provider: Any,
        config: Optional[RetryConfig] = None,
        max_retries: Optional[int] = None,
        on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    ) -> None:
        self.provider = provider
        self.config = config or RetryConfig()
        if max_retries is not None:
            self.config.max_retries = max_retries
        self.on_retry = on_retry

        # Track statistics
        self._total_retries = 0
        self._total_calls = 0

    def __getattr__(self, name: str) -> Any:
        r"""Delegate attribute access to underlying provider."""
        return getattr(self.provider, name)

    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        r"""Execute a function with retry logic.

        Args:
            func (`Callable`):
                The async function to execute.
            *args:
                Positional arguments for the function.
            **kwargs:
                Keyword arguments for the function.

        Returns:
            The result of the function.

        Raises:
            Exception: The last exception if all retries fail.

        Example:
            >>> import asyncio
            >>> async def flaky_func():
            ...     return "success"
            >>> resilient = ResilientProvider(None)
            >>> # asyncio.run(resilient.execute_with_retry(flaky_func))
        """
        self._total_calls += 1
        last_exception: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except self.config.retryable_exceptions as e:
                last_exception = e

                if attempt >= self.config.max_retries:
                    logger.error(
                        "All %d retries exhausted for %s: %s",
                        self.config.max_retries,
                        func.__name__,
                        e,
                    )
                    raise

                wait_time = self.config.calculate_wait(attempt)
                self._total_retries += 1

                logger.warning(
                    "Retry %d/%d for %s after %.2fs: %s",
                    attempt + 1,
                    self.config.max_retries,
                    func.__name__,
                    wait_time,
                    e,
                )

                if self.on_retry:
                    self.on_retry(attempt, e, wait_time)

                await asyncio.sleep(wait_time)

        # Should not reach here, but for type safety
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected retry loop exit")

    def execute_sync_with_retry(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        r"""Execute a synchronous function with retry logic.

        Args:
            func (`Callable`):
                The sync function to execute.
            *args:
                Positional arguments for the function.
            **kwargs:
                Keyword arguments for the function.

        Returns:
            The result of the function.

        Raises:
            Exception: The last exception if all retries fail.
        """
        self._total_calls += 1
        last_exception: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return func(*args, **kwargs)

            except self.config.retryable_exceptions as e:
                last_exception = e

                if attempt >= self.config.max_retries:
                    logger.error(
                        "All %d retries exhausted for %s: %s",
                        self.config.max_retries,
                        func.__name__,
                        e,
                    )
                    raise

                wait_time = self.config.calculate_wait(attempt)
                self._total_retries += 1

                logger.warning(
                    "Retry %d/%d for %s after %.2fs: %s",
                    attempt + 1,
                    self.config.max_retries,
                    func.__name__,
                    wait_time,
                    e,
                )

                if self.on_retry:
                    self.on_retry(attempt, e, wait_time)

                time.sleep(wait_time)

        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected retry loop exit")

    def stats(self) -> dict:
        r"""Get retry statistics.

        Returns:
            `dict`: Dictionary with total_calls, total_retries, retry_rate.

        Example:
            >>> resilient = ResilientProvider(None)
            >>> stats = resilient.stats()
            >>> "total_calls" in stats
            True
        """
        return {
            "total_calls": self._total_calls,
            "total_retries": self._total_retries,
            "retry_rate": (self._total_retries / self._total_calls if self._total_calls > 0 else 0.0),
        }

    def reset_stats(self) -> None:
        r"""Reset retry statistics."""
        self._total_retries = 0
        self._total_calls = 0
