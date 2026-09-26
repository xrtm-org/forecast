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

r"""Tests for reasoning-model support, telemetry extraction, and structured output."""

from types import SimpleNamespace
from typing import Any, Tuple

import pytest

from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.core.exceptions import EmptyContentError
from xrtm.forecast.providers.inference.openai_provider import OpenAIProvider


@pytest.fixture(autouse=True)
def _disable_disk_cache(monkeypatch):
    """Keep provider tests deterministic: no shared .cache/inference.db."""
    monkeypatch.setenv("FORECAST_CACHE_ENABLED", "false")


class FakeAsyncCompletions:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[dict] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.response


def build_provider(response: Any, **config_kwargs: Any) -> Tuple[OpenAIProvider, FakeAsyncCompletions]:
    provider = OpenAIProvider(OpenAIConfig(model_id="deepseek-flash", api_key="fake", **config_kwargs))
    completions = FakeAsyncCompletions(response)
    provider.client = SimpleNamespace(  # type: ignore[assignment]
        chat=SimpleNamespace(completions=completions)
    )
    return provider, completions


def completion(
    content: str = "ok",
    reasoning: str | None = None,
    usage: Any = None,
    finish_reason: str = "stop",
) -> Any:
    message = SimpleNamespace(content=content, tool_calls=None, reasoning_content=reasoning)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish_reason)],
        usage=usage,
    )


@pytest.mark.asyncio
async def test_thinking_disabled_is_sent_via_extra_body():
    provider, completions = build_provider(completion(), thinking="disabled")
    result = await provider.generate_content_async("hi")
    assert completions.calls[0]["extra_body"] == {"thinking": {"type": "disabled"}}
    assert result.text == "ok"


@pytest.mark.asyncio
async def test_thinking_auto_sends_no_extra_body():
    provider, completions = build_provider(completion())
    await provider.generate_content_async("hi")
    assert "extra_body" not in completions.calls[0]


@pytest.mark.asyncio
async def test_empty_content_with_reasoning_raises():
    provider, _ = build_provider(completion(content="", reasoning="thinking hard", finish_reason="length"))
    with pytest.raises(EmptyContentError, match="reasoning_content"):
        await provider.generate_content_async("hi")


@pytest.mark.asyncio
async def test_usage_captures_cached_and_reasoning_tokens():
    usage = SimpleNamespace(
        prompt_tokens=100,
        completion_tokens=20,
        total_tokens=120,
        prompt_tokens_details=SimpleNamespace(cached_tokens=64),
        completion_tokens_details=SimpleNamespace(reasoning_tokens=12),
    )
    provider, _ = build_provider(completion(usage=usage))
    result = await provider.generate_content_async("hi")
    assert result.usage["cached_prompt_tokens"] == 64
    assert result.usage["reasoning_tokens"] == 12


@pytest.mark.asyncio
async def test_usage_falls_back_to_deepseek_cache_fields():
    usage = SimpleNamespace(
        prompt_tokens=10,
        completion_tokens=2,
        total_tokens=12,
        prompt_cache_hit_tokens=8,
    )
    provider, _ = build_provider(completion(usage=usage))
    result = await provider.generate_content_async("hi")
    assert result.usage["cached_prompt_tokens"] == 8


@pytest.mark.asyncio
async def test_response_format_is_forwarded():
    provider, completions = build_provider(completion())
    await provider.generate_content_async("hi", response_format={"type": "json_object"})
    assert completions.calls[0]["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_reasoning_content_is_exposed_in_metadata_when_content_present():
    provider, _ = build_provider(completion(content="final", reasoning="chain of thought"))
    result = await provider.generate_content_async("hi")
    assert result.metadata["reasoning_content"] == "chain of thought"
