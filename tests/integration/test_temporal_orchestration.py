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

from datetime import datetime

import pytest

from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.schemas.graph import BaseGraphState, TemporalContext


@pytest.mark.asyncio
async def test_orchestrator_clock_mocking_integration():
    # Setup node that checks time
    async def check_time_node(state, report):
        state.node_reports["detected"] = datetime.now()
        return None

    orch = Orchestrator.create_standard()
    orch.add_node("check", check_time_node)
    orch.set_entry_point("check")

    # Define historical time
    historical = datetime(1999, 12, 31, 23, 59)
    state = BaseGraphState(
        subject_id="y2k", temporal_context=TemporalContext(reference_time=historical, is_backtest=True)
    )

    await orch.run(state)

    detected = state.node_reports["detected"]
    assert detected.year == 1999
    assert detected.month == 12
    assert detected.day == 31


@pytest.mark.asyncio
async def test_parallel_clock_mocking_integration():
    async def check_time_worker(state, name):
        state.node_reports[name] = datetime.now()
        return None

    orch = Orchestrator.create_standard()
    orch.add_node("w1", lambda s, r: check_time_worker(s, "w1"))
    orch.add_node("w2", lambda s, r: check_time_worker(s, "w2"))
    orch.add_parallel_group("workers", ["w1", "w2"])
    orch.set_entry_point("workers")

    historical = datetime(2030, 1, 1)
    state = BaseGraphState(
        subject_id="future", temporal_context=TemporalContext(reference_time=historical, is_backtest=True)
    )

    await orch.run(state)

    assert state.node_reports["w1"].year == 2030
    assert state.node_reports["w2"].year == 2030
