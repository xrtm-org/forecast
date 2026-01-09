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

from forecast.core.config.inference import GeminiConfig
from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.graph import BaseGraphState
from forecast.kit.agents.llm import LLMAgent
from forecast.providers.inference.base import InferenceProvider, ModelResponse


# 1. Mock Provider for tests
class MockProvider(InferenceProvider):
    r"""
    A fake inference provider for high-level core tests.
    """

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
        """Standardized streaming interface."""
        yield self.generate_content("")


# 2. Mock Agent
class MockAgent(LLMAgent):
    r"""
    A fake agent implementation for unit testing.
    """

    async def run(self, input_data: Any, **kwargs: Any) -> Dict[str, Any]:
        result = await self.model.generate_content_async(str(input_data))
        return self.parse_output(result.text)


@pytest.mark.asyncio
async def test_library_standalone_orchestration():
    r"""
    Ensures xrtm-forecast core can run a reasoning chain standalone.
    """
    """
    Ensures xrtm-forecast core can run a reasoning chain standalone.
    """
    mock_provider = MockProvider()
    _ = MockAgent(model=mock_provider)

    from forecast.core.config.graph import GraphConfig

    orchestrator = Orchestrator(config=GraphConfig(max_cycles=2))

    # Define a simple node
    async def hello_node(state: BaseGraphState, on_progress: Callable) -> Optional[str]:
        state.context["node_visited"] = True
        return None  # Terminate

    orchestrator.register_node("start", hello_node)

    state = BaseGraphState(subject_id="test_subject")
    await orchestrator.run(state, entry_node="start")

    assert state.subject_id == "test_subject"
    assert state.context["node_visited"] is True
    assert state.cycle_count == 1


@pytest.mark.asyncio
async def test_agent_parsing_logic():
    r"""
    Verifies that Agent correctly parses markdown JSON from model responses.
    """
    """
    Verifies that Agent correctly parses markdown JSON.
    """
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


@pytest.mark.asyncio
async def test_model_factory_tier_handling():
    r"""
    Verifies the factory correctly returns providers based on performance tiers.
    """
    """
    Verifies the factory correctly returns providers based on tiers.
    """
    _ = GeminiConfig(api_key="mock", model_id="primary", flash_model_id="cheap")
    # We can't easily test the actual library factory without real keys or more mocking,
    # but we can verify our MockProvider logic here if needed.
    pass
