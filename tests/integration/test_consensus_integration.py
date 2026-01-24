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

r"""Integration tests for RecursiveConsensus topology."""

from typing import Any

import pytest

from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.kit.topologies.consensus import RecursiveConsensus


@pytest.mark.asyncio
async def test_full_consensus_pipeline_with_ivw():
    r"""Verifies the E2E flow: Analysts -> IVW Aggregator -> Supervisor."""

    # 1. Define analyst that provides both confidence and uncertainty
    async def mock_analyst(state: BaseGraphState, reporter: Any) -> None:
        outputs = state.context.get("analyst_outputs", [])
        # We give each analyst slightly different data
        idx = len(outputs)
        outputs.append(
            {
                "confidence": 0.5 + (0.1 * idx),
                "uncertainty": 0.1,
                "reasoning": f"Analyst {idx} reasoning",
            }
        )
        state.context["analyst_outputs"] = outputs
        return None

    # 2. Define supervisor that approves based on aggregated confidence
    async def mock_supervisor(state: BaseGraphState, reporter: Any) -> None:
        agg = state.context.get("aggregate", {})
        if agg.get("confidence", 0.0) >= 0.5:
            state.context["decision"] = "APPROVE"
        else:
            state.context["decision"] = "REVISE"
        return None

    # 3. Build topology
    topology = RecursiveConsensus(
        analyst_wrappers=[mock_analyst, mock_analyst],
        supervisor_wrapper=mock_supervisor,
        use_ivw=True,
    )
    orch = topology.build_graph()

    # 4. Run
    initial_state = BaseGraphState(subject_id="integration_test")
    final_state = await orch.run(initial_state)

    # 5. Assertions
    assert "aggregator" in final_state.execution_path
    assert "supervisor" in final_state.execution_path
    assert final_state.context["decision"] == "APPROVE"

    # Verify IVW result structure
    agg = final_state.context.get("aggregate", {})
    assert "confidence" in agg
    assert "uncertainty" in agg
    assert agg["method"] == "inverse_variance_weighting"
    assert agg["n_inputs"] == 2


@pytest.mark.asyncio
async def test_consensus_revision_loop():
    r"""Verifies that the revision loop actually repeats analysis."""

    # State toggle to simulate improvement after revision
    async def mock_analyst(state: BaseGraphState, reporter: Any) -> None:
        outputs = state.context.get("analyst_outputs", [])
        # Orchestrator increments cycle_count BEFORE executing the first node.
        # analyst is Node 1.
        # Pass 1: cycle_count is 1. We want REVISE.
        # Pass 2: cycle_count is 4. We want APPROVE.
        conf = 0.4 if state.cycle_count < 2 else 0.8
        outputs.append({"confidence": conf, "uncertainty": 0.05})
        state.context["analyst_outputs"] = outputs
        return None

    async def mock_supervisor(state: BaseGraphState, reporter: Any) -> None:
        agg = state.context.get("aggregate", {})
        if agg.get("confidence", 0.0) >= 0.7:
            state.context["decision"] = "APPROVE"
        else:
            state.context["decision"] = "REVISE"
        # Must clear outputs for the next pass
        state.context["analyst_outputs"] = []
        return None

    topology = RecursiveConsensus(
        analyst_wrappers=[mock_analyst],
        supervisor_wrapper=mock_supervisor,
        use_ivw=True,
        max_cycles=1,  # 1 revision aloud, max_node_visits will be (1+1)*10 = 20
    )
    orch = topology.build_graph()

    final_state = await orch.run(BaseGraphState(subject_id="loop_test"))

    # Pass 1: analyst(1), aggregator(2), supervisor(3) -> REVISE
    # Pass 2: analyst(4), aggregator(5), supervisor(6) -> APPROVE
    assert final_state.cycle_count >= 6
    execution_str = " -> ".join(final_state.execution_path)
    assert execution_str.count("aggregator") == 2
    assert final_state.context["decision"] == "APPROVE"
