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

import json
import logging

import pytest

from xrtm.forecast.core.exceptions import ForecastParseError
from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from xrtm.forecast.providers.inference.base import InferenceProvider, ModelResponse


class LegacyProvider(InferenceProvider):
    r"""Provider-free payload compatible with the released xrtm 0.3.0 example."""

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return ModelResponse(
            text=json.dumps(
                {
                    "probability": 0.877,
                    "reasoning": "Deterministic provider-free forecast for legacy payload.",
                    "logical_trace": [
                        {
                            "event": "deterministic_real_corpus_prior",
                            "probability": 0.877,
                            "description": "Stable hash-derived probability for product smoke validation.",
                        }
                    ],
                    "structural_trace": ["load_question", "provider_free_forecast", "validate_output"],
                }
            )
        )

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return self.generate_content(prompt, output_logprobs, **kwargs)

    async def stream(self, messages, **kwargs):
        yield self.generate_content("")


class ExplicitIntervalProvider(InferenceProvider):
    r"""Provider that already supplies an explicit interval."""

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return ModelResponse(
            text=json.dumps(
                {
                    "probability": 0.61,
                    "confidence_interval": {"low": 0.5, "high": 0.7, "level": 0.8},
                    "reasoning": "Structured payload.",
                }
            )
        )

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return self.generate_content(prompt, output_logprobs, **kwargs)

    async def stream(self, messages, **kwargs):
        yield self.generate_content("")


@pytest.mark.asyncio
async def test_forecasting_analyst_backfills_missing_confidence_interval(caplog):
    r"""Legacy provider-free payloads should not trigger schema validation warnings."""

    agent = ForecastingAnalyst(model=LegacyProvider())

    with caplog.at_level(logging.WARNING):
        result = await agent.run("Will the provider-free example stay schema-clean?")

    assert result.probability == pytest.approx(0.877)
    assert result.confidence_interval is not None
    assert result.confidence_interval.model_dump() == {"low": 0.777, "high": 0.977, "level": 0.9}
    assert "Schema validation failed" not in caplog.text


@pytest.mark.asyncio
async def test_forecasting_analyst_preserves_explicit_confidence_interval():
    r"""Explicit intervals from providers should remain unchanged."""

    agent = ForecastingAnalyst(model=ExplicitIntervalProvider())

    result = await agent.run("Will explicit confidence intervals survive parsing?")

    assert result.confidence_interval is not None
    assert result.confidence_interval.model_dump() == {"low": 0.5, "high": 0.7, "level": 0.8}


class TelemetryProvider(InferenceProvider):
    r"""Provider that supplies usage and cache metadata."""

    model_id = "deepseek-flash"

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return ModelResponse(
            text=json.dumps(
                {
                    "probability": 0.7,
                    "reasoning": "Structured reasoning.",
                }
            ),
            usage={
                "prompt_tokens": 120,
                "completion_tokens": 40,
                "total_tokens": 160,
                "cached_prompt_tokens": 96,
            },
            metadata={"cache_hit": True},
        )

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return self.generate_content(prompt, output_logprobs, **kwargs)

    async def stream(self, messages, **kwargs):
        yield self.generate_content("")


class GarbageProvider(InferenceProvider):
    r"""Provider that returns unparseable text."""

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return ModelResponse(text="this is not json")

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return self.generate_content(prompt, output_logprobs, **kwargs)

    async def stream(self, messages, **kwargs):
        yield self.generate_content("")


@pytest.mark.asyncio
async def test_analyst_records_parse_status_and_telemetry():
    agent = ForecastingAnalyst(model=TelemetryProvider())
    result = await agent.run("Will telemetry be recorded?")

    assert result.parse_status == "ok"
    assert result.probability == pytest.approx(0.7)
    assert result.usage.prompt_tokens == 120
    assert result.usage.cached_prompt_tokens == 96
    assert result.provenance is not None
    assert result.provenance.cache_hit is True
    assert result.provenance.model_id == "deepseek-flash"
    assert result.provenance.prompt_id == "analyst-default"


@pytest.mark.asyncio
async def test_analyst_flags_invalid_json_without_raising():
    agent = ForecastingAnalyst(model=GarbageProvider())
    result = await agent.run("Will invalid json be flagged?")

    assert result.parse_status == "invalid_json"
    assert result.probability == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_analyst_strict_parse_raises():
    agent = ForecastingAnalyst(model=GarbageProvider(), strict_parse=True)
    with pytest.raises(ForecastParseError):
        await agent.run("Will strict parsing raise?")


class SignedGraphProvider(InferenceProvider):
    r"""Provider returning a causal graph with a signed (inhibitory) edge."""

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return ModelResponse(
            text=json.dumps(
                {
                    "probability": 0.6,
                    "reasoning": "Signed graph.",
                    "causal_nodes": [
                        {"node_id": "n1", "event": "A", "probability": 0.6},
                        {"node_id": "n2", "event": "B", "probability": 0.5},
                    ],
                    "causal_edges": [{"source": "n1", "target": "n2", "weight": -0.5}],
                }
            )
        )

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return self.generate_content(prompt, output_logprobs, **kwargs)

    async def stream(self, messages, **kwargs):
        yield self.generate_content("")


class BadGraphProvider(InferenceProvider):
    r"""Provider whose causal graph references an unknown node."""

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return ModelResponse(
            text=json.dumps(
                {
                    "probability": 0.6,
                    "reasoning": "Broken graph.",
                    "causal_nodes": [{"node_id": "n1", "event": "A", "probability": 0.6}],
                    "causal_edges": [{"source": "n1", "target": "n9", "weight": 0.3}],
                }
            )
        )

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs):
        return self.generate_content(prompt, output_logprobs, **kwargs)

    async def stream(self, messages, **kwargs):
        yield self.generate_content("")


@pytest.mark.asyncio
async def test_analyst_preserves_signed_edge_weights():
    result = await ForecastingAnalyst(model=SignedGraphProvider()).run("Signed edges?")
    assert result.logical_edges[0].weight == pytest.approx(-0.5)


@pytest.mark.asyncio
async def test_analyst_reports_graph_issues_without_failing():
    result = await ForecastingAnalyst(model=BadGraphProvider()).run("Broken graph?")

    assert result.parse_status == "ok"
    assert result.metadata.raw_data["graph_issues"]
    assert any("n9" in issue for issue in result.metadata.raw_data["graph_issues"])


@pytest.mark.asyncio
async def test_analyst_strict_dag_raises():
    from xrtm.forecast.core.exceptions import GraphError

    agent = ForecastingAnalyst(model=BadGraphProvider(), strict_dag=True)
    with pytest.raises(GraphError):
        await agent.run("Broken graph?")


@pytest.mark.asyncio
async def test_analyst_prompt_template_sets_prompt_id():
    from xrtm.forecast.core.schemas.prompt import PromptTemplate

    template = PromptTemplate(prompt_id="orb-v2", system_prompt="Custom persona.")
    agent = ForecastingAnalyst(model=TelemetryProvider(), prompt_template=template)
    result = await agent.run("Custom prompt?")

    assert result.provenance is not None
    assert result.provenance.prompt_id == "orb-v2"
