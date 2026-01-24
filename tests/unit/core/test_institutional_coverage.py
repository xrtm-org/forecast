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
from unittest.mock import AsyncMock

import pytest

from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.runtime import AsyncRuntime
from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.core.utils.parser import parse_json_markdown


@pytest.mark.asyncio
async def test_orchestrator_institutional_features():
    """Verify Orchestrator progress reporting and cycle triggers."""
    orch = Orchestrator.create_standard(max_cycles=2)

    # Test register_node alias
    m = AsyncMock(return_value=None)
    orch.register_node("start", m)
    orch.set_entry_point("start")

    # Test on_progress callback
    progress_mock = AsyncMock()
    state = BaseGraphState(subject_id="test_sub")
    await orch.run(state, on_progress=progress_mock)

    assert progress_mock.called
    assert state.cycle_count == 1

    # Test max_cycles termination
    orch.add_node("loop", AsyncMock(return_value="loop"))
    orch.set_entry_point("loop")
    state = BaseGraphState(subject_id="test_loop")
    await orch.run(state)
    assert state.cycle_count == 2


@pytest.mark.asyncio
async def test_runtime_institutional_features():
    """Verify AsyncRuntime performance and naming hooks."""
    # Test task name accessor
    name = AsyncRuntime.current_task_name()
    assert isinstance(name, str)

    # Test sleep
    await AsyncRuntime.sleep(0.001)

    # Test task group (structured concurrency)
    async with AsyncRuntime.task_group() as tg:
        t1 = tg.create_task(asyncio.sleep(0.001))
    assert t1.done()


def test_parser_institutional_robustness():
    """Verify JSON parser against LLM conversational noise."""
    # Case 1: Markdown JSON
    md = 'Here is the data: ```json\n{"score": 0.9}\n```'
    assert parse_json_markdown(md)["score"] == 0.9

    # Case 2: Brackets fallback
    noise = "Check this: [1, 2, 3] some text after"
    assert parse_json_markdown(noise) == [1, 2, 3]

    # Case 3: Naked JSON
    naked = '{"key": "val"}'
    assert parse_json_markdown(naked)["key"] == "val"

    # Case 4: Failure with default
    bad = "not json"
    assert parse_json_markdown(bad, default={}) == {}
