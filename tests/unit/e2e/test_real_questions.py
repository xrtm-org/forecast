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

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from xrtm.data.corpora import load_real_binary_questions

from xrtm.forecast.core.schemas.forecast import ForecastOutput, MetadataBase
from xrtm.forecast.e2e.real_questions import (
    ForecastOutputValidationError,
    parse_llm_forecast_payload,
    run_real_question_e2e,
    validate_forecast_output_integrity,
)
from xrtm.forecast.providers.inference.base import InferenceProvider, ModelResponse


class FakeProvider(InferenceProvider):
    model_id = "fake-local-openai-compatible"
    base_url = "http://localhost:8080/v1"

    def generate_content(self, prompt: Any, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        raw = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(reasoning_content="hidden model reasoning"))]
        )
        return ModelResponse(
            text='''<think>private chain</think>
```json
{
  "probability": "62%",
  "reasoning": "Rates were elevated but a pause was plausible.",
  "logical_trace": [{"event": "central bank setup", "probability": 0.62, "description": "Policy context"}],
  "structural_trace": ["load_question", "local_llm_forecast", "validate_output"]
}
```''',
            raw=raw,
            usage={"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
        )

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        return self.generate_content(prompt, output_logprobs, **kwargs)

    async def stream(self, messages, **kwargs):
        yield self.generate_content(messages, **kwargs)


class ReasoningOnlyProvider(FakeProvider):
    def __init__(self) -> None:
        self.max_token_requests: list[int] = []

    def generate_content(self, prompt: Any, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        self.max_token_requests.append(kwargs["max_tokens"])
        if len(self.max_token_requests) < 3:
            raw = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(reasoning_content="thinking without final json"))]
            )
            return ModelResponse(text="", raw=raw, usage={"completion_tokens": kwargs["max_tokens"]})

        raw = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        reasoning_content='''analysis before the final answer
```json
{
  "probability": 0.37,
  "reasoning": "Reasoning-only backends may place the final answer in reasoning_content.",
  "logical_trace": [{"event": "reasoning only", "probability": 0.37, "description": "JSON was emitted outside content"}],
  "structural_trace": ["load_question", "local_llm_forecast", "validate_output"]
}
```'''
                    )
                )
            ]
        )
        return ModelResponse(text="", raw=raw, usage={"completion_tokens": kwargs["max_tokens"]})


def test_parse_llm_forecast_payload_strips_qwen_reasoning_and_fences() -> None:
    payload = parse_llm_forecast_payload(
        '<think>reason privately</think>\n```json\n{"probability": 0.41, "reasoning": "visible"}\n```'
    )

    assert payload["probability"] == 0.41
    assert payload["reasoning"] == "visible"
    assert payload["qwen_reasoning"] == "reason privately"


def test_real_question_e2e_builds_valid_records_without_provider_network(tmp_path) -> None:
    records = run_real_question_e2e(
        limit=1,
        provider=FakeProvider(),
        artifact_dir=Path("output/unit-real-e2e"),
        write_artifacts=False,
    )

    assert len(records) == 1
    question = load_real_binary_questions(limit=1)[0]
    record = records[0]
    assert record.question_id == question.id
    assert record.output.question_id == question.id
    assert record.output.probability == 0.62
    assert record.output.metadata.created_at is not None
    assert record.output.metadata.snapshot_time == question.metadata.snapshot_time
    assert record.output.reasoning_trace["causal_graph"]["nodes"]
    assert record.provider_metadata["usage"]["total_tokens"] == 7


def test_real_question_e2e_retries_reasoning_only_responses() -> None:
    provider = ReasoningOnlyProvider()

    records = run_real_question_e2e(limit=1, provider=provider, max_tokens=512, write_artifacts=False)

    assert provider.max_token_requests == [512, 2048, 4096]
    assert records[0].output.probability == 0.37
    assert records[0].output.reasoning.startswith("Reasoning-only backends")
    assert records[0].output.metadata.raw_data["qwen_reasoning_present"] is True


def test_validate_forecast_output_integrity_rejects_bad_question_id() -> None:
    question = load_real_binary_questions(limit=1)[0]
    output = ForecastOutput(
        question_id="wrong",
        probability=0.5,
        reasoning="A valid explanation.",
        logical_trace=[],
        structural_trace=[],
        metadata=MetadataBase(snapshot_time=question.metadata.snapshot_time),
    )

    with pytest.raises(ForecastOutputValidationError, match="question_id mismatch"):
        validate_forecast_output_integrity(question, output)
