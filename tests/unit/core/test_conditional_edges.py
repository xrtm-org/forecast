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

from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.schemas.graph import BaseGraphState


@pytest.mark.asyncio
async def test_conditional_routing():
    """Verify state-based dynamic routing."""
    orch = Orchestrator.create_standard()

    # Nodes
    async def start(state, _):
        state.context["value"] = "HIGH"
        return None

    async def node_b(state, _):
        state.execution_path.append("B")
        return None

    async def node_c(state, _):
        state.execution_path.append("C")
        return None

    orch.add_node("start", start)
    orch.add_node("node_b", node_b)
    orch.add_node("node_c", node_c)

    # Conditional Logic
    def route_logic(state):
        if state.context.get("value") == "HIGH":
            return "high_path"
        return "low_path"

    orch.add_conditional_edge("start", route_logic, {"high_path": "node_b", "low_path": "node_c"})

    # Run 1: High Path
    state = BaseGraphState(subject_id="test1")
    final = await orch.run(state, entry_node="start")
    assert "B" in final.execution_path
    assert "C" not in final.execution_path


@pytest.mark.asyncio
async def test_conditional_fallback():
    """Verify fallback if condition fails or returns unknown key (logs warning, stops branch)."""
    orch = Orchestrator.create_standard()

    async def no_op(state, _):
        return None

    orch.add_node("start", no_op)

    def bad_logic(state):
        return "unknown_key"

    orch.add_conditional_edge("start", bad_logic, {"valid": "end"})

    state = BaseGraphState(subject_id="test2")
    final = await orch.run(state, entry_node="start")

    # Should perform 'start' then stop because no valid next node
    assert len(final.execution_path) == 1
    assert final.execution_path[0] == "start"
