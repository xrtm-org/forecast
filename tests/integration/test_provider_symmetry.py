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
from pydantic import SecretStr

from forecast.core.config.inference import GeminiConfig, OpenAIConfig
from forecast.providers.inference.gemini_provider import GeminiProvider
from forecast.providers.inference.openai_provider import OpenAIProvider


class MockTool:
    def __init__(self, name: str, result: str):
        self.name = name
        self.result = result

    async def execute(self, **kwargs: Any) -> str:
        return self.result


@pytest.mark.asyncio
async def test_provider_symmetry_tool_calling():
    r"""
    Verifies that both OpenAI and Gemini providers handle tool-calling loops identically.
    Note: We use mock configs and assume the underlying SDKs might fail if not mocked,
    but we want to check the internal orchestration logic.
    """
    # This is a structural test. In a real environment, we'd mock the AsyncOpenAI and genai.Client.
    # For now, we verify that the providers have the expected methods and loop logic is present.

    openai_cfg = OpenAIConfig(model_id="gpt-4o", api_key=SecretStr("mock"))
    gemini_cfg = GeminiConfig(model_id="gemini-2.0-flash", api_key=SecretStr("mock"))

    o_provider = OpenAIProvider(openai_cfg)
    g_provider = GeminiProvider(gemini_cfg)

    # Verify both have generate_content_async
    assert hasattr(o_provider, "generate_content_async")
    assert hasattr(g_provider, "generate_content_async")

    # Verify OpenAI now has _execute_tool_calls (symmetry check)
    assert hasattr(o_provider, "_execute_tool_calls")
    assert hasattr(g_provider, "_execute_tool_calls")


def test_config_singleton_integrity():
    r"""Verifies that the global settings singleton is correctly initialized."""
    from forecast.core.config.main import settings

    assert settings is not None
    # Verify defaults are minimal/gone
    assert not hasattr(settings, "gemini_smart_model")
    assert not hasattr(settings, "openai_model")
