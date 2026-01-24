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

from unittest.mock import AsyncMock, MagicMock

import pytest

from xrtm.forecast.kit.agents.routing import RoutingAgent
from xrtm.forecast.providers.inference.base import ModelResponse


@pytest.mark.asyncio
async def test_routing_agent_logic():
    r"""Verifies that RoutingAgent correctly classifies and dispatches tasks."""
    router_model = MagicMock()

    fast_agent = MagicMock()
    fast_agent.run = AsyncMock(return_value="fast_result")

    smart_agent = MagicMock()
    smart_agent.run = AsyncMock(return_value="smart_result")

    agent = RoutingAgent(router_model=router_model, fast_tier=fast_agent, smart_tier=smart_agent)

    # 1. Test FAST path
    router_model.run = AsyncMock(return_value=ModelResponse(text="FAST"))
    result = await agent.run("simple task")
    assert result == "fast_result"
    fast_agent.run.assert_called_with("simple task")

    # 2. Test SMART path
    router_model.run = AsyncMock(return_value=ModelResponse(text="SMART"))
    result = await agent.run("complex reasoning task")
    assert result == "smart_result"
    smart_agent.run.assert_called_with("complex reasoning task")


@pytest.mark.asyncio
async def test_routing_agent_fallback():
    r"""Verifies that RoutingAgent falls back to available routes if decision fails."""
    router_model = MagicMock()
    router_model.run = AsyncMock(side_effect=Exception("Router down"))

    smart_agent = MagicMock()
    smart_agent.run = AsyncMock(return_value="fallback_result")

    agent = RoutingAgent(router_model=router_model, smart_tier=smart_agent)

    result = await agent.run("any task")
    assert result == "fallback_result"
    smart_agent.run.assert_called_once()
