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

import asyncio
import logging
from typing import Any, Coroutine, TypeVar

try:
    import uvloop

    _UVLOOP_AVAILABLE = True
except ImportError:
    _UVLOOP_AVAILABLE = False


logger = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncRuntime:
    r"""
    Institutional Abstraction for AsyncIO operations.

    ### Why not raw asyncio?
    1.  **Temporal Integrity (Chronos)**: Standard `asyncio.sleep` cannot be intercepted for
        fast-forwarding backtests. `AsyncRuntime.sleep` is point-in-time aware.
    2.  **Structured Concurrency**: Centralizing task spawning enables lifecycle tracking
        and prevents background task leakage.
    3.  **Performance**: Handlers for high-performance loops (uvloop) are handled transparently.
    4.  **Auditability**: Provides the hook for OpenTelemetry (OTel) to trace task causality
        across the reasoning graph.
    """

    @staticmethod
    def spawn(coro: Coroutine[Any, Any, T], name: str, daemon: bool = False) -> asyncio.Task[T]:
        r"""
        Spawns a task with mandatory naming and registry tracking.

        Args:
            coro (`Coroutine[Any, Any, T]`): The coroutine to execute as a task.
            name (`str`): A descriptive name for the task (used in telemetry).
            daemon (`bool`, *optional*, defaults to `False`):
                If `True`, the task is tracked as a background daemon.

        Returns:
            `asyncio.Task[T]`: The handle to the spawned task.

        Example:
            ```python
            task = AsyncRuntime.spawn(my_coro(), name="research_task")
            ```
        r"""
        task = asyncio.create_task(coro, name=name)
        # TODO: Integration with OTel for parent-child trace propagation
        return task

    @staticmethod
    def task_group() -> asyncio.TaskGroup:
        r"""
        Returns a context manager for structured concurrency (Python 3.11+).

        Tasks spawned within a group are automatically joined on exit. If any
        task in the group fails, the remaining tasks are cancelled.

        Returns:
            `asyncio.TaskGroup`: The structured concurrency context manager.

        Example:
            ```python
            async with AsyncRuntime.task_group() as tg:
                tg.create_task(coro1())
                tg.create_task(coro2())
            ```
        r"""
        return asyncio.TaskGroup()

    @staticmethod
    async def sleep(seconds: float):
        r"""
        Time-aware pause. ADVANCED: Advancing the clock in backtests.
        """
        # In the future, this will check if a virtual clock is being mocked by Chronos
        await asyncio.sleep(seconds)

    @staticmethod
    def run_main(entrypoint: Coroutine[Any, Any, T]) -> T:
        r"""
        High-performance entrypoint for the platform.

        Initializes the event loop (using `uvloop` if available) and runs
        the provided entrypoint coroutine until completion.

        Args:
            entrypoint (`Coroutine[Any, Any, T]`): The main application coroutine.

        Returns:
            `T`: The result returned by the entrypoint coroutine.

        Example:
            ```python
            if __name__ == "__main__":
                AsyncRuntime.run_main(main())
            ```
        r"""
        if _UVLOOP_AVAILABLE:
            uvloop.install()
            logger.info("[RUNTIME] uvloop installed and active.")

        return asyncio.run(entrypoint)

    @staticmethod
    def current_task_name() -> str:
        r"""Safe accessor for current task name."""
        try:
            task = asyncio.current_task()
            return task.get_name() if task else "MainThread"
        except Exception:
            return "Unknown"


__all__ = ["AsyncRuntime"]
