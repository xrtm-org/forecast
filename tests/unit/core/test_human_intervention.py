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

from forecast.core.interfaces import HumanProvider
from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.graph import BaseGraphState


@pytest.mark.asyncio
async def test_human_intervention_orchestration():
    r"""Verifies that the orchestrator correctly pauses and resumes for human input."""

    # 1. Setup Mock Human Provider
    mock_provider = AsyncMock(spec=HumanProvider)
    mock_provider.get_human_input.return_value = "Human judgment: High probability."

    # 2. Setup Orchestrator with a human node
    orch = Orchestrator()
    prompt = "Please review the sentiment. Is it bullish?"
    human_node = f"human:{prompt}"

    # Mock a research node
    async def research_step(state, *args):
        return "AI is bullish."

    orch.add_node("research", research_step)
    orch.add_node(human_node, None)  # Orchestrator handles human: nodes automatically
    orch.add_edge("research", human_node)
    orch.set_entry_point("research")

    # 3. Setup State
    state = BaseGraphState(subject_id="test_hitl")
    state.context["human_provider"] = mock_provider

    # 4. Execute
    final_state = await orch.run(state)

    # 5. Assertions
    assert "research" in final_state.execution_path
    assert human_node in final_state.execution_path
    assert final_state.node_reports[human_node] == "Human judgment: High probability."
    assert mock_provider.get_human_input.called
    assert mock_provider.get_human_input.call_args[0][0] == prompt
    # Verify Merkle anchoring worked for hitl
    assert final_state.state_hash is not None
