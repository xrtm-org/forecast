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

from forecast.core.schemas.graph import BaseGraphState
from forecast.kit.topologies.consensus import RecursiveConsensus


@pytest.mark.asyncio
async def test_recursive_consensus_flow():
    """Verify the topology loops once then finishes."""

    # Mocks
    async def analyst_1(state, _):
        state.context.setdefault("analyst_1_calls", 0)
        state.context["analyst_1_calls"] += 1
        return None

    async def analyst_2(state, _):
        state.context.setdefault("analyst_2_calls", 0)
        state.context["analyst_2_calls"] += 1
        return None

    async def aggregator(state, _):
        state.execution_path.append("AGGR")
        return None

    async def supervisor(state, _):
        calls = state.context["analyst_1_calls"]
        if calls < 2:
            state.context["decision"] = "REVISE"
        else:
            state.context["decision"] = "APPROVE"
        state.execution_path.append("SUP")
        return None

    # Build
    topo = RecursiveConsensus(
        analyst_wrappers=[analyst_1, analyst_2],
        supervisor_wrapper=supervisor,
        aggregator_wrapper=aggregator,
        max_cycles=10,
    )
    orch = topo.build_graph()

    # Run
    state = BaseGraphState(subject_id="consensus_test")
    final = await orch.run(state)

    # Check calls: Should run twice (Loop 1: Revise, Loop 2: Approve)
    assert final.context["analyst_1_calls"] == 2
    assert final.context["analyst_2_calls"] == 2

    # Check Path
    # [parallel:.., AGGR, SUP, parallel:.., AGGR, SUP]
    path_str = ",".join(final.execution_path)
    assert path_str.count("AGGR") == 2
    assert path_str.count("SUP") == 2
