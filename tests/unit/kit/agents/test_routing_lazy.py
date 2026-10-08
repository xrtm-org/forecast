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

r"""RoutingAgent must not require an OpenAI key when tiers are supplied."""

import asyncio


class _FakeAgent:
    async def run(self, input_data, **kwargs):
        return "smart-result"


def test_routing_agent_constructs_without_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from xrtm.forecast.kit.agents.routing import RoutingAgent

    agent = RoutingAgent(smart_tier=_FakeAgent())
    assert agent.router_model is None


def test_routing_agent_falls_back_to_smart_without_router(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from xrtm.forecast.kit.agents.routing import RoutingAgent

    agent = RoutingAgent(smart_tier=_FakeAgent())
    assert asyncio.run(agent.run("classify something complex")) == "smart-result"
