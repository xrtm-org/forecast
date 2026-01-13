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

import pytest

from forecast.core.runtime import AsyncRuntime


class TestAsyncRuntime:
    r"""Unit tests for the AsyncRuntime facade."""

    @pytest.mark.asyncio
    async def test_spawn_tracking(self):
        """Verify that spawned tasks are named correctly."""

        async def dummy():
            return "done"

        task = AsyncRuntime.spawn(dummy(), name="test_task")
        assert task.get_name() == "test_task"
        res = await task
        assert res == "done"

    @pytest.mark.asyncio
    async def test_current_task_name(self):
        """Verify safe accessor for task name."""

        async def worker():
            return AsyncRuntime.current_task_name()

        task = AsyncRuntime.spawn(worker(), name="my_worker")
        name = await task
        assert name == "my_worker"

    @pytest.mark.asyncio
    async def test_sleep(self):
        """Verify sleep wrapper works (basic smoke test)."""
        # We can't easily test time travel here without mocking,
        # but we verify it doesn't crash.
        await AsyncRuntime.sleep(0.01)
