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

import importlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from xrtm.forecast.core.schemas.forecast import ForecastOutput, MetadataBase
from xrtm.forecast.providers.inference.base import InferenceProvider, ModelResponse

if importlib.util.find_spec("xrtm.data.corpora") is None:
    pytest.skip("xrtm.data.corpora is not available until the data corpus release lands", allow_module_level=True)

real_corpus = importlib.import_module("xrtm.data.corpora")
load_real_binary_questions = real_corpus.load_real_binary_questions
real_questions = importlib.import_module("xrtm.forecast.e2e.real_questions")
build_real_question_prompt = real_questions.build_real_question_prompt
ForecastOutputValidationError = real_questions.ForecastOutputValidationError
parse_llm_forecast_payload = real_questions.parse_llm_forecast_payload
run_real_question_e2e = real_questions.run_real_question_e2e
validate_forecast_output_integrity = real_questions.validate_forecast_output_integrity


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
  "execution_trace": ["load_question", "local_llm_forecast", "validate_output"]
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
  "execution_trace": ["load_question", "local_llm_forecast", "validate_output"]
}
```'''
                    )
                )
            ]
        )
        return ModelResponse(text="", raw=raw, usage={"completion_tokens": kwargs["max_tokens"]})


class RepairingReasoningProvider(FakeProvider):
    def __init__(self) -> None:
        self.max_token_requests: list[int] = []

    def generate_content(self, prompt: Any, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        self.max_token_requests.append(kwargs["max_tokens"])
        if isinstance(prompt, list) and "Convert these forecast notes into JSON" in prompt[-1]["content"]:
            raw = SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            reasoning_content='''Formatting the notes.
{"step": "calculate_gap", "description": "Assessed the market move required."}
```json
{
  "probability": 0.38,
  "reasoning": "The target required a sizable Q4 rally with mixed macro support.",
  "logical_trace": [{"event": "market_gap_analysis", "probability": 0.38, "description": "Required move versus prevailing conditions"}],
  "execution_trace": ["load_question", "local_llm_forecast", "validate_output"]
}
```'''
                        )
                    )
                ]
            )
            return ModelResponse(text="", raw=raw, usage={"completion_tokens": kwargs["max_tokens"]})

        raw = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        reasoning_content=(
                            "Working through the forecast notes without producing final JSON yet. "
                            "Probability looks closer to 0.38 because the rally requirement is large."
                        )
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


def test_parse_llm_forecast_payload_prefers_forecast_shaped_object() -> None:
    payload = parse_llm_forecast_payload(
        '''{"step": "calculate_gap", "description": "intermediate note"}
```json
{"probability": 0.38, "reasoning": "final answer", "logical_trace": [{"event": "driver", "probability": 0.38, "description": "why"}], "execution_trace": ["load_question", "local_llm_forecast", "validate_output"]}
```'''
    )

    assert payload["probability"] == 0.38
    assert payload["reasoning"] == "final answer"


def test_build_real_question_prompt_allows_background_knowledge_before_snapshot() -> None:
    question = load_real_binary_questions(limit=1)[0]

    prompt = build_real_question_prompt(question)
    normalized = " ".join(prompt[1]["content"].split())

    assert len(prompt) == 2
    assert prompt[0]["role"] == "system"
    assert prompt[1]["role"] == "user"
    assert "background world knowledge available before the snapshot time" in normalized
    assert "do not use information learned after the snapshot time" in normalized
    assert "using only the information below" not in normalized


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
    assert record.output.structural_trace == ["load_question", "local_llm_forecast", "validate_output"]
    assert record.provider_metadata["usage"]["total_tokens"] == 7


def test_real_question_e2e_accepts_reasoning_graph_alias() -> None:
    question = load_real_binary_questions(limit=1)[0]

    response = ModelResponse(
        text="""{
  \"probability\": 0.44,
  \"reasoning_trace\": {
    \"narrative\": \"A moderate move remains plausible.\",
    \"reasoning_graph\": {
      \"nodes\": [{\"event\": \"macro backdrop\", \"probability\": 0.44, \"description\": \"mixed inputs\"}]
    }
  },
  \"execution_trace\": [\"load_question\", \"local_llm_forecast\", \"validate_output\"]
}""",
        usage={},
    )

    output = real_questions._build_output_from_response(
        question,
        response,
        FakeProvider(),
        corpus_id=real_corpus.REAL_BINARY_CORPUS_ID,
    )

    assert output.reasoning == "A moderate move remains plausible."
    assert output.logical_trace[0].event == "macro backdrop"
    assert output.structural_trace == ["load_question", "local_llm_forecast", "validate_output"]


def test_real_question_e2e_retries_reasoning_only_responses() -> None:
    provider = ReasoningOnlyProvider()

    records = run_real_question_e2e(limit=1, provider=provider, max_tokens=512, write_artifacts=False)

    assert provider.max_token_requests == [512, 2048, 4096]
    assert records[0].output.probability == 0.37
    assert records[0].output.reasoning.startswith("Reasoning-only backends")
    assert records[0].output.metadata.raw_data["qwen_reasoning_present"] is True


def test_real_question_e2e_repairs_reasoning_notes_into_forecast_json() -> None:
    provider = RepairingReasoningProvider()

    records = run_real_question_e2e(limit=1, provider=provider, max_tokens=512, write_artifacts=False)

    assert provider.max_token_requests == [512, 2048, 4096, 2048]
    assert records[0].output.probability == 0.38
    assert records[0].output.reasoning.startswith("The target required")


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
