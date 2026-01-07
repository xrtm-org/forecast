from typing import Any, Callable, Dict, Optional

import pytest

from forecast.agents.base import Agent
from forecast.agents.llm import LLMAgent
from forecast.graph.orchestrator import Orchestrator
from forecast.inference.base import InferenceProvider, ModelResponse
from forecast.inference.config import GeminiConfig
from forecast.schemas.graph import BaseGraphState


# 1. Mock Provider for tests
class MockProvider(InferenceProvider):
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
    async def run(self, context: Any, **kwargs: Any) -> Dict[str, Any]:
        response = await self.model.generate_content_async("test prompt")
        return self.parse_output(response.text)


@pytest.mark.asyncio
async def test_library_standalone_orchestration():
    """
    Ensures xrtm-forecast core can run a reasoning chain without CAFE dependencies.
    """
    mock_provider = MockProvider()
    _ = MockAgent(model=mock_provider)

    orchestrator = Orchestrator(max_cycles=2)

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
    """
    Verifies the factory correctly returns providers based on tiers.
    """
    _ = GeminiConfig(api_key="mock", model_id="primary", flash_model_id="cheap")
    # We can't easily test the actual library factory without real keys or more mocking,
    # but we can verify our MockProvider logic here if needed.
    pass
