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

from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.core.tools.base import Tool
from xrtm.forecast.kit.agents.fact_checker import FactCheckerAgent


class MockSearchTool(Tool):
    @property
    def name(self):
        return "mock_search"

    @property
    def description(self):
        return "Mocks search results"

    @property
    def parameters_schema(self):
        return {}

    async def run(self, temporal_context=None, query: str = "") -> str:
        if "sky is blue" in query:
            return "Reference: The sky is widely considered verified blue."
        return "No information found."


@pytest.mark.asyncio
async def test_fact_checker_verifies_claim():
    """Verify agent calls tool and updates score."""
    tool = MockSearchTool()
    agent = FactCheckerAgent(tools=[tool])

    state = BaseGraphState(subject_id="fc_test")
    state.context["claims"] = ["The sky is blue", "Unicorns exist"]

    final_state = await agent.run(state)

    results = final_state.context["fact_check_results"]
    assert len(results) == 2

    # Claim 1: Sky -> Verified
    assert results[0]["claim"] == "The sky is blue"
    assert results[0]["verified"] is True

    # Claim 2: Unicorns -> Not Verified
    assert results[1]["claim"] == "Unicorns exist"
    assert results[1]["verified"] is False

    # Score: 1/2 = 0.5
    assert final_state.context["verification_score"] == 0.5
