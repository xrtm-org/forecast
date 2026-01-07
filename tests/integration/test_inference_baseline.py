from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from forecast.inference.config import GeminiConfig, OpenAIConfig
from forecast.inference.factory import ModelFactory


def test_gemini_provider_instantiation():
    config = GeminiConfig(
        model_id="gemini-2.0-flash",
        api_key=SecretStr("mock-key"),
        redis_url=None,  # Disable rate limiter for test
    )
    provider = ModelFactory.get_provider(config)
    assert provider.model_id == "gemini-2.0-flash"
    assert provider.supports_tools is True


def test_openai_provider_instantiation():
    config = OpenAIConfig(model_id="gpt-4o", api_key=SecretStr("mock-key"))
    provider = ModelFactory.get_provider(config)
    assert provider.model_id == "gpt-4o"


@pytest.mark.asyncio
async def test_openai_generate_mock():
    with patch("forecast.inference.openai_provider.AsyncOpenAI") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response from OpenAI (gpt-4o): Simulation Mode."
        mock_response.usage.prompt_tokens = 0
        mock_response.usage.completion_tokens = 0
        mock_response.usage.total_tokens = 0
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        config = OpenAIConfig(model_id="gpt-4o", api_key=SecretStr("mock-key"))
        provider = ModelFactory.get_provider(config)
        response = await provider.generate_content_async("Hello")
        assert "OpenAI" in response.text
        assert "Simulation Mode" in response.text
