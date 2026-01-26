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

from unittest.mock import AsyncMock

import pytest

from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.schemas.graph import BaseGraphState


@pytest.mark.asyncio
async def test_orchestrator_error_paths() -> None:
    r"""Test error handling and edge cases in Orchestrator."""
    orch = Orchestrator.create_standard()
    state = BaseGraphState(subject_id="test_errors")

    # 1. Unknown node in parallel group (Line 279)
    orch.add_parallel_group("group1", ["non_existent"])
    orch.set_entry_point("group1")
    await orch.run(state)  # Should log error and continue/break safely

    # 2. Error in parallel node (Lines 300-301)
    async def failing_node(s, p):
        raise ValueError("Parallel fail")

    orch.nodes = {}  # Reset
    orch.add_node("fail", failing_node)
    orch.add_parallel_group("group2", ["fail"])
    orch.set_entry_point("group2")
    await orch.run(state)  # Should catch exception and log

    # 3. Human intervention without provider (Lines 246-249)
    state.context = {}  # Ensure no human_provider
    orch.set_entry_point("human:how are you?")
    await orch.run(state)  # Should log error and break

    # 4. Conditional edge logic failure (Lines 324-325)
    def failing_condition(s):
        raise RuntimeError("Condition fail")

    orch.add_node("start", AsyncMock(return_value=None))
    orch.add_conditional_edge("start", failing_condition, {"ok": "end"})
    orch.set_entry_point("start")
    await orch.run(state)

    # 5. Unknown flow control (Lines 308-309)
    # We can trigger this by having a node in edges that isn't in nodes/groups
    orch.edges = {"start": "ghost_node"}
    orch.set_entry_point("start")
    await orch.run(state)


@pytest.mark.asyncio
async def test_orchestrator_usage_aggregation_robustness() -> None:
    r"""Test usage aggregation with malformed data (Lines 353-368)."""
    orch = Orchestrator.create_standard()
    state = BaseGraphState(subject_id="test_usage")

    # Test with non-integer usage
    bad_output = {"usage": {"prompt_tokens": "invalid", "completion_tokens": None}}
    orch.aggregate_usage(state, bad_output)

    assert state.usage["prompt_tokens"] == 0

    # Test with non-dict usage
    orch.aggregate_usage(state, "not a dict")
    assert state.usage["prompt_tokens"] == 0


@pytest.mark.asyncio
async def test_orchestrator_none_node(caplog) -> None:
    r"""Test line 232-233 where node function is None."""
    orch = Orchestrator.create_standard()
    orch.nodes["bad"] = None  # type: ignore
    orch.set_entry_point("bad")
    state = BaseGraphState(subject_id="test_none")
    await orch.run(state)
    assert "Unknown node (function is None)" in caplog.text
