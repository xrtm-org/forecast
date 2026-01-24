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

r"""Unit tests for the Red Team Agent."""

import pytest

from xrtm.forecast.kit.agents.red_team import CounterArgument, RedTeamAgent


class MockInferenceProvider:
    r"""Mock provider for testing."""

    async def generate(self, prompt: str) -> "MockResponse":
        return MockResponse(
            """COUNTER_ARGUMENT: The employment data is a lagging indicator.
Historical patterns show that rate hikes often precede recessions.

WEAKNESSES:
- Relies too heavily on employment data
- Ignores yield curve inversion signals
- Assumes Fed will ignore market stress
- No consideration of global economic headwinds

ALTERNATIVE_PROBABILITY: 0.45
CHALLENGE_CONFIDENCE: 0.75"""
        )

    async def run(self, prompt: str) -> "MockResponse":
        return await self.generate(prompt)


class MockResponse:
    def __init__(self, text: str) -> None:
        self.text = text


@pytest.fixture
def mock_model() -> MockInferenceProvider:
    return MockInferenceProvider()


class TestCounterArgument:
    r"""Tests for CounterArgument schema."""

    def test_creation(self) -> None:
        r"""Test basic CounterArgument creation."""
        counter = CounterArgument(
            original_thesis="Test thesis",
            counter_argument="Test counter",
            weakness_points=["Point 1", "Point 2"],
            alternative_probability=0.3,
            confidence_in_challenge=0.8,
        )
        assert counter.original_thesis == "Test thesis"
        assert len(counter.weakness_points) == 2
        assert counter.alternative_probability == 0.3

    def test_probability_bounds(self) -> None:
        r"""Test that probabilities are bounded 0-1."""
        with pytest.raises(ValueError):
            CounterArgument(
                original_thesis="Test",
                counter_argument="Test",
                alternative_probability=1.5,  # Invalid
            )


class TestRedTeamAgent:
    r"""Tests for RedTeamAgent functionality."""

    @pytest.mark.asyncio
    async def test_challenge_generates_counter_argument(self, mock_model: MockInferenceProvider) -> None:
        r"""Test that challenge() generates a valid counter-argument."""
        agent = RedTeamAgent(model=mock_model)  # type: ignore

        result = await agent.challenge(
            thesis="The Fed will raise rates (80% confidence)",
            reasoning="Employment data is strong and inflation remains elevated.",
        )

        assert isinstance(result, CounterArgument)
        assert result.original_thesis == "The Fed will raise rates (80% confidence)"
        assert "employment" in result.counter_argument.lower() or "lagging" in result.counter_argument.lower()
        assert len(result.weakness_points) >= 3
        assert result.alternative_probability == 0.45
        assert result.confidence_in_challenge == 0.75

    @pytest.mark.asyncio
    async def test_intensity_levels(self, mock_model: MockInferenceProvider) -> None:
        r"""Test that different intensity levels affect the prompt."""
        mild_agent = RedTeamAgent(model=mock_model, intensity="mild")  # type: ignore
        aggressive_agent = RedTeamAgent(model=mock_model, intensity="aggressive")  # type: ignore

        mild_prompt = mild_agent._build_challenge_prompt("Test", "Reasoning")
        aggressive_prompt = aggressive_agent._build_challenge_prompt("Test", "Reasoning")

        assert "Respectfully" in mild_prompt
        assert "Demolish" in aggressive_prompt

    @pytest.mark.asyncio
    async def test_run_method_integration(self, mock_model: MockInferenceProvider) -> None:
        r"""Test that run() integrates with BaseGraphState."""
        from xrtm.forecast.core.schemas.graph import BaseGraphState

        agent = RedTeamAgent(model=mock_model)  # type: ignore

        state = BaseGraphState(subject_id="test_question")
        state.context["current_thesis"] = "Rate hike imminent"
        state.context["current_reasoning"] = "Strong employment"

        result_state = await agent.run(state)

        assert "red_team_counter" in result_state.context
        assert result_state.context["red_team_counter"] is not None
        assert agent.name in result_state.node_reports
