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

from typing import Any

import pytest

from xrtm.forecast.kit.agents.base import Agent
from xrtm.forecast.kit.skills.definitions import BaseSkill


class MockSkill(BaseSkill):
    r"""
    A minimal skill implementation for unit testing.
    """

    @property
    def name(self) -> str:
        return "mock_skill"

    @property
    def description(self) -> str:
        return "A fake skill for testing"

    async def execute(self, **kwargs: Any) -> Any:
        return f"Hello {kwargs.get('name', 'World')}"


class SimpleAgent(Agent):
    r"""
    A minimal agent implementation for unit testing.
    """

    async def run(self, input_data: Any, **kwargs: Any) -> Any:
        return input_data


def test_agent_add_skill():
    r"""
    Verifies that skills can be correctly added to an agent.
    """
    agent = SimpleAgent(name="TestAgent")
    skill = MockSkill()

    agent.add_skill(skill)
    assert "mock_skill" in agent.skills
    assert agent.get_skill("mock_skill") == skill


@pytest.mark.asyncio
async def test_skill_execution():
    r"""
    Verifies that a skill's execute method works as expected.
    """
    skill = MockSkill()
    result = await skill.execute(name="Antigravity")
    assert result == "Hello Antigravity"
