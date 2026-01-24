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

import pytest

from xrtm.forecast import AsyncRuntime


@pytest.mark.asyncio
async def test_runtime_task_group():
    r"""Verifies that the AsyncRuntime.task_group() works as expected."""
    results = []

    async def worker(val: int):
        await AsyncRuntime.sleep(0.01)
        results.append(val)

    async with AsyncRuntime.task_group() as tg:
        tg.create_task(worker(1))
        tg.create_task(worker(2))

    # TaskGroup ensures tasks are finished before exiting scope
    assert len(results) == 2
    assert set(results) == {1, 2}


@pytest.mark.asyncio
async def test_runtime_spawn():
    r"""Verifies that AsyncRuntime.spawn() creates a named task."""

    async def dummy():
        await asyncio.sleep(0.1)

    task = AsyncRuntime.spawn(dummy(), name="VerificationTask")
    assert "VerificationTask" in task.get_name()
    await task


def test_runtime_main_entrypoint():
    r"""
    Note: We can't easily test run_main inside pytest because it starts a new loop.
    But we can verify the top-level export and structure.
    """
    assert hasattr(AsyncRuntime, "run_main")
    assert hasattr(AsyncRuntime, "sleep")
    assert hasattr(AsyncRuntime, "spawn")
