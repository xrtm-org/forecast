from typing import Any

import pytest

from forecast.agents.base import Agent
from forecast.skills.definitions import BaseSkill


class MockSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "mock_skill"

    @property
    def description(self) -> str:
        return "A fake skill for testing"

    async def execute(self, **kwargs: Any) -> Any:
        return f"Hello {kwargs.get('name', 'World')}"

class SimpleAgent(Agent):
    async def run(self, input_data: Any, **kwargs: Any) -> Any:
        return input_data

def test_agent_add_skill():
    agent = SimpleAgent(name="TestAgent")
    skill = MockSkill()

    agent.add_skill(skill)
    assert "mock_skill" in agent.skills
    assert agent.get_skill("mock_skill") == skill

@pytest.mark.asyncio
async def test_skill_execution():
    skill = MockSkill()
    result = await skill.execute(name="Antigravity")
    assert result == "Hello Antigravity"
