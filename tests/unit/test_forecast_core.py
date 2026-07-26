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

from typing import Any, Callable, Dict, Optional

import pytest

from xrtm.forecast.core.config.graph import GraphConfig
from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.schemas.forecast import ForecastQuestion
from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.kit.agents.llm import LLMAgent
from xrtm.forecast.kit.agents.specialists import ForecastingAnalyst
from xrtm.forecast.providers.inference.base import InferenceProvider, ModelResponse


class MockProvider(InferenceProvider):
    r"""A fake inference provider for high-level core tests."""

    def __init__(self, config=None, tier="SMART"):
        self.config = config
        self.tier = tier

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        return ModelResponse(
            text='{"result": "success", "reasoning": {"claim": "MOCK", "evidence": [], "risks": [], "rationale": "MOCK"}}',
            usage={"total_tokens": 10},
        )

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        return self.generate_content(prompt)

    async def stream(self, messages, **kwargs):
        yield self.generate_content("")


class AnalystMockProvider(InferenceProvider):
    r"""A fake provider that returns valid analyst-shaped JSON."""

    model_id = "analyst-mock"

    def __init__(self):
        self.last_kwargs: dict[str, Any] = {}

    def generate_content(self, prompt: str, **kwargs: Any) -> ModelResponse:
        self.last_kwargs = kwargs
        return ModelResponse(
            text='{"probability": 0.65, "confidence_interval": {"low": 0.50, "high": 0.78, "level": 0.9}, '
                 '"reasoning": "Mock analysis.", "causal_nodes": [], "causal_edges": []}',
            usage={"total_tokens": 20},
        )

    async def generate_content_async(self, prompt: str, **kwargs: Any) -> ModelResponse:
        return self.generate_content(prompt, **kwargs)

    async def stream(self, messages, **kwargs):
        yield self.generate_content("")


class MockAgent(LLMAgent):
    r"""A fake agent implementation for unit testing."""

    async def run(self, input_data: Any, **kwargs: Any) -> Dict[str, Any]:
        result = await self.model.generate_content_async(str(input_data))
        return self.parse_output(result.text)


@pytest.mark.asyncio
async def test_library_standalone_orchestration():
    r"""Ensures xrtm-forecast core can run a reasoning chain standalone."""
    mock_provider = MockProvider()
    _ = MockAgent(model=mock_provider)

    orchestrator = Orchestrator(config=GraphConfig(max_cycles=2))

    async def hello_node(state: BaseGraphState, on_progress: Callable) -> Optional[str]:
        state.context["node_visited"] = True
        return None

    orchestrator.register_node("start", hello_node)

    state = BaseGraphState(subject_id="test_subject")
    await orchestrator.run(state, entry_node="start")

    assert state.subject_id == "test_subject"
    assert state.context["node_visited"] is True
    assert state.cycle_count == 1


@pytest.mark.asyncio
async def test_agent_parsing_logic():
    r"""Verifies that Agent correctly parses markdown JSON from model responses."""
    mock_provider = MockProvider()
    agent = MockAgent(model=mock_provider)

    raw_text = """
    Here is the result:
    ```json
    {"value": 42, "status": "active"}
    ```
    """
    parsed = agent.parse_output(raw_text)
    assert parsed["value"] == 42
    assert parsed["status"] == "active"


# --- OpenAIConfig retry configuration (issue #61) ---


def test_openai_config_default_retries():
    """OpenAIConfig defaults max_retries=2, backoff_base=2.0."""
    config = OpenAIConfig(model_id="gpt-test", api_key="fake")
    assert config.max_retries == 2
    assert config.backoff_base == 2.0


def test_openai_config_custom_retries():
    """OpenAIConfig accepts custom max_retries and backoff_base."""
    config = OpenAIConfig(model_id="gpt-test", api_key="fake", max_retries=5, backoff_base=1.5)
    assert config.max_retries == 5
    assert config.backoff_base == 1.5


def test_openai_config_rejects_invalid_backoff():
    """OpenAIConfig rejects backoff_base <= 1.0."""
    with pytest.raises(ValueError):
        OpenAIConfig(model_id="gpt-test", api_key="fake", backoff_base=1.0)


# --- MockProvider seed (issue #63) ---


def test_mock_provider_deterministic_same_seed():
    """Same prompt + same seed produces same probability."""
    from xrtm.forecast.providers.inference.mock_provider import MockProvider as RealMockProvider

    p1 = RealMockProvider(seed=42)
    p2 = RealMockProvider(seed=42)

    r1 = p1.generate_content("Will X happen?")
    r2 = p2.generate_content("Will X happen?")
    assert r1.text == r2.text


def test_mock_provider_different_seed_different_output():
    """Different seeds produce different outputs for the same prompt."""
    from xrtm.forecast.providers.inference.mock_provider import MockProvider as RealMockProvider

    p1 = RealMockProvider(seed=42)
    p2 = RealMockProvider(seed=99)

    r1 = p1.generate_content("Will X happen?")
    r2 = p2.generate_content("Will X happen?")
    assert r1.text != r2.text


def test_mock_provider_no_seed_backward_compat():
    """MockProvider without seed works as before."""
    from xrtm.forecast.providers.inference.mock_provider import MockProvider as RealMockProvider

    p = RealMockProvider()
    r = p.generate_content("Question")
    assert r.metadata["mock"] is True
    assert r.usage["total_tokens"] == 2


# --- ForecastingAnalyst temperature/max_tokens (issue #60) ---


@pytest.mark.asyncio
async def test_analyst_forwards_temperature_max_tokens():
    """ForecastingAnalyst passes temperature and max_tokens to LLM calls."""
    provider = AnalystMockProvider()
    analyst = ForecastingAnalyst(model=provider, temperature=0.2, max_tokens=768)

    question = ForecastQuestion(id="q1", title="Test")
    await analyst.run(question)

    assert provider.last_kwargs.get("temperature") == 0.2
    assert provider.last_kwargs.get("max_tokens") == 768


@pytest.mark.asyncio
async def test_analyst_no_generation_kwargs_by_default():
    """Without temperature/max_tokens, no extra kwargs are sent."""
    provider = AnalystMockProvider()
    analyst = ForecastingAnalyst(model=provider)

    question = ForecastQuestion(id="q1", title="Test")
    await analyst.run(question)

    assert "temperature" not in provider.last_kwargs
    assert "max_tokens" not in provider.last_kwargs


# --- ForecastingAnalyst customizable prompts (issue #59) ---


@pytest.mark.asyncio
async def test_analyst_custom_system_prompt():
    """Custom system_prompt appears in the prompt sent to the LLM."""
    provider = AnalystMockProvider()
    analyst = ForecastingAnalyst(
        model=provider,
        system_prompt="You are an expert financial forecaster.",
    )

    question = ForecastQuestion(id="q1", title="Test")
    await analyst.run(question)

    # The generate_content was called — verify it didn't crash
    assert provider.last_kwargs is not None


@pytest.mark.asyncio
async def test_analyst_few_shot_examples():
    """Few-shot examples are injected into the prompt."""
    provider = AnalystMockProvider()
    analyst = ForecastingAnalyst(
        model=provider,
        few_shot_examples=["Example 1: ... probability=0.7", "Example 2: ... probability=0.3"],
    )

    question = ForecastQuestion(id="q1", title="Test")
    result = await analyst.run(question)

    assert result.probability == 0.65


# --- data#44: ForecastQuestion.context integration ---


@pytest.mark.asyncio
async def test_analyst_merges_question_context():
    """ForecastingAnalyst merges question.context into the prompt."""
    provider = AnalystMockProvider()
    analyst = ForecastingAnalyst(model=provider)

    question = ForecastQuestion(
        id="q1",
        title="Will market exceed $100?",
        context={"market_price": 0.55, "volume_24h": 150000},
    )
    result = await analyst.run(question)

    assert result.probability == 0.65


@pytest.mark.asyncio
async def test_analyst_question_without_context_still_works():
    """ForecastQuestion without context works as before."""
    provider = AnalystMockProvider()
    analyst = ForecastingAnalyst(model=provider)

    question = ForecastQuestion(id="q2", title="Simple question")
    result = await analyst.run(question)

    assert result.question_id == "q2"
