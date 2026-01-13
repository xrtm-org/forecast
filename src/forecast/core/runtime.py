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

    This facade enforces:
    1.  **Safety**: Prevents "Fire and Forget" orphan tasks by centralized tracking (future).
    2.  **Performance**: Automatically installs `uvloop` if available.
    3.  **Observability**: Provides hooks for task telemetry (start/end times).
    4.  **Time Travel**: Wraps `sleep` to allow Chronos protocols to fast-forward time.
    r"""

    @staticmethod
    def spawn(coro: Coroutine[Any, Any, T], name: str, daemon: bool = False) -> asyncio.Task[T]:
        r"""
        Spawns a standard asyncio Task with mandatory naming.

        Args:
            coro: The coroutine to execute.
            name: A descriptive name for the task (required for debugging).
            daemon: If True, this task is considered background logic (telemetry tag).

        Returns:
            The created `asyncio.Task`.
        """
        # In the future, we can add a 'parent_id' here or register to a global TaskGroup.
        task = asyncio.create_task(coro, name=name)

        # Simple debug logging
        # logger.debug(f"[RUNTIME] Spawning task: {name}")
        return task

    @staticmethod
    async def sleep(seconds: float):
        r"""
        Pauses execution. Wraps `asyncio.sleep`.

        **Chronos Note**: In the future, this method will check the `TemporalContext`.
        If we are in a backtest, it might skip the sleep or advance the virtual clock instantly.
        """
        await asyncio.sleep(seconds)

    @staticmethod
    def run_main(entrypoint: Coroutine[Any, Any, T]) -> T:
        r"""
        Entrypoint for the application. Installs uvloop if available.
        """
        if _UVLOOP_AVAILABLE:
            uvloop.install()
            logger.info("[RUNTIME] uvloop installed and active.")
        else:
            logger.warning("[RUNTIME] uvloop not found. Falling back to standard asyncio.")

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
