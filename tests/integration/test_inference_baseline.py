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

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from forecast.core.config.inference import GeminiConfig, OpenAIConfig
from forecast.providers.inference.factory import ModelFactory


def test_gemini_provider_instantiation():
    r"""
    Verifies that the ModelFactory correctly instantiates a GeminiProvider.
    """
    config = GeminiConfig(
        model_id="gemini-2.0-flash",
        api_key=SecretStr("mock-key"),
        redis_url=None,  # Disable rate limiter for test
    )
    provider = ModelFactory.get_provider(config)
    assert provider.model_id == "gemini-2.0-flash"
    assert provider.supports_tools is True


def test_openai_provider_instantiation():
    r"""
    Verifies that the ModelFactory correctly instantiates an OpenAIProvider.
    """
    config = OpenAIConfig(model_id="gpt-4o", api_key=SecretStr("mock-key"))
    provider = ModelFactory.get_provider(config)
    assert provider.model_id == "gpt-4o"


@pytest.mark.asyncio
async def test_openai_generate_mock():
    r"""
    Verifies the OpenAI provider's async generation using a client mock.
    """
    with patch("forecast.providers.inference.openai_provider.AsyncOpenAI") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response from OpenAI (gpt-4o): Simulation Mode."
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage.prompt_tokens = 0
        mock_response.usage.completion_tokens = 0
        mock_response.usage.total_tokens = 0
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        config = OpenAIConfig(model_id="gpt-4o", api_key=SecretStr("mock-key"))
        provider = ModelFactory.get_provider(config)
        response = await provider.generate_content_async("Hello")
        assert "OpenAI" in response.text
        assert "Simulation Mode" in response.text
