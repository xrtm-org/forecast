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

from forecast.core.config.graph import GraphConfig
from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.graph import BaseGraphState
from forecast.kit.scenarios import ScenarioManager


class SimpleState(BaseGraphState):
    r"""A minimal Pydantic state for scenario branching tests."""
    value: int
    multiplier: int = 1


async def multiply_stage(state: SimpleState, on_progress=None) -> None:
    state.value = state.value * state.multiplier
    return None


@pytest.mark.asyncio
async def test_scenario_manager_execution():
    """Verify that multiple branches run in parallel with distinct states."""

    # 1. Setup Graph with simpler configuration
    config = GraphConfig(max_cycles=10)

    orchestrator = Orchestrator(config)
    orchestrator.add_node("process", multiply_stage)
    orchestrator.set_entry_point("process")
    # Finish logic is implicit or via edge; for this simple test, logic terminates naturally
    # or we can verify cycle count.
    # The default running logic will stop if no next node, which is what `multiply_stage` implies
    # as it returns state but no next step directive.

    # 2. Setup Manager
    manager = ScenarioManager(orchestrator)
    manager.add_branch("control", overrides={"multiplier": 2})  # 10 * 2 = 20
    manager.add_branch("treatment", overrides={"multiplier": 3})  # 10 * 3 = 30

    # 3. Validation Logic
    initial_state = SimpleState(value=10, subject_id="test-scenario")

    results = await manager.run_all(initial_state)

    # 4. Assertions
    assert "control" in results
    assert "treatment" in results

    assert results["control"].value == 20
    assert results["treatment"].value == 30

    # Ensure initial state wasn't mutated in place
    assert initial_state.value == 10
