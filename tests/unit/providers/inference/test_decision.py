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

r"""Tests for typed decision providers."""

import json
from typing import Any

import pytest

from xrtm.forecast.core.exceptions import ConfigurationError, ProviderError
from xrtm.forecast.core.interfaces import InferenceProvider
from xrtm.forecast.core.schemas.decision import DecisionOption
from xrtm.forecast.providers.inference.base import ModelResponse
from xrtm.forecast.providers.inference.decision import JevProvider, LLMDecisionProvider

OPTIONS = [DecisionOption(name="trade", description="Open position"), DecisionOption(name="skip")]


class ScriptedProvider(InferenceProvider):
    r"""Provider that returns a canned text payload and records kwargs."""

    def __init__(self, text: str, usage: dict | None = None):
        self.text = text
        self.usage = usage or {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        self.last_kwargs: dict = {}

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        self.last_kwargs = kwargs
        return ModelResponse(text=self.text, usage=self.usage)

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        return self.generate_content(prompt, output_logprobs, **kwargs)

    async def stream(self, messages: Any, **kwargs: Any):
        yield self.generate_content("")


def decision_payload(**overrides: Any) -> str:
    payload = {
        "decision": "trade",
        "confidence": 0.8,
        "probabilities": {"trade": 0.8, "skip": 0.2},
        "escalate": False,
        "rationale": "edge is clear",
    }
    payload.update(overrides)
    return json.dumps(payload)


@pytest.mark.asyncio
async def test_llm_decision_provider_parses_and_normalizes():
    provider = ScriptedProvider(decision_payload())
    result = await LLMDecisionProvider(model=provider).decide("Should we trade?", OPTIONS)

    assert result.decision == "trade"
    assert result.confidence == pytest.approx(0.8)
    assert result.probabilities == {"trade": pytest.approx(0.8), "skip": pytest.approx(0.2)}
    assert result.usage["prompt_tokens"] == 10
    assert "response_format" in provider.last_kwargs


@pytest.mark.asyncio
async def test_llm_decision_normalizes_unnormalized_probabilities():
    provider = ScriptedProvider(decision_payload(probabilities={"trade": 4, "skip": 1}))
    result = await LLMDecisionProvider(model=provider).decide("Should we trade?", OPTIONS)
    assert result.probabilities["trade"] == pytest.approx(0.8)
    assert result.probabilities["skip"] == pytest.approx(0.2)


@pytest.mark.asyncio
async def test_llm_decision_falls_back_to_highest_probability_option():
    provider = ScriptedProvider(decision_payload(decision="not-an-option"))
    result = await LLMDecisionProvider(model=provider).decide("Should we trade?", OPTIONS)
    assert result.decision == "trade"


@pytest.mark.asyncio
async def test_llm_decision_rejects_non_json():
    provider = ScriptedProvider("I would rather not decide.")
    with pytest.raises(ProviderError):
        await LLMDecisionProvider(model=provider).decide("Should we trade?", OPTIONS)


@pytest.mark.asyncio
async def test_llm_decision_requires_options():
    provider = ScriptedProvider(decision_payload())
    with pytest.raises(ConfigurationError):
        await LLMDecisionProvider(model=provider).decide("Should we trade?", [])


@pytest.mark.asyncio
async def test_jev_provider_unwraps_answers_envelope():
    jev_payload = json.dumps(
        {
            "answers": {
                "intent": {
                    "type": "choice",
                    "choice": "trade",
                    "confidence": 0.97,
                    "probabilities": {"trade": 0.97, "skip": 0.03},
                }
            }
        }
    )
    scripted = ScriptedProvider(jev_payload)
    provider = JevProvider(provider=scripted)
    result = await provider.decide("Should we trade?", OPTIONS)

    assert result.decision == "trade"
    assert result.confidence == pytest.approx(0.97)
    assert result.probabilities["skip"] == pytest.approx(0.03)


def test_jev_provider_requires_gateway_configuration(monkeypatch):
    monkeypatch.delenv("JEV_BASE_URL", raising=False)
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        JevProvider()
