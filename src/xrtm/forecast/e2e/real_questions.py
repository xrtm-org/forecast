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

r"""Real-question local-LLM E2E harness.

The harness intentionally consumes the deterministic ``xrtm-data`` real binary
corpus and only calls the explicitly configured local OpenAI-compatible provider.
It never fetches question data from the network.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, SecretStr
from xrtm.data.corpora import REAL_BINARY_CORPUS_ID, load_real_binary_questions

from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.core.schemas.forecast import CausalNode, ForecastOutput, ForecastQuestion, MetadataBase
from xrtm.forecast.providers.inference.base import InferenceProvider, ModelResponse
from xrtm.forecast.providers.inference.factory import ModelFactory

_THINK_BLOCK_RE = re.compile(r"<think>\s*(.*?)\s*</think>", re.IGNORECASE | re.DOTALL)
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)
_ALLOWED_ARTIFACT_ROOTS = {"output", ".pytest_cache", ".cache", "logs"}


class ForecastOutputValidationError(ValueError):
    r"""Raised when a generated ``ForecastOutput`` is structurally invalid."""


class ForecastHarnessRecord(BaseModel):
    r"""Serializable runtime record emitted by the real-question E2E harness."""

    question_id: str
    output: ForecastOutput
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def default_artifact_dir() -> Path:
    r"""Return the ignored default directory for real-question E2E artifacts."""
    return Path(os.getenv("XRTM_FORECAST_REAL_E2E_ARTIFACT_DIR", "output/real-e2e"))


def build_real_question_prompt(question: ForecastQuestion) -> list[dict[str, str]]:
    r"""Build a bounded, offline forecasting prompt for one corpus question."""
    snapshot_time = question.metadata.snapshot_time.isoformat()
    content = question.description or ""
    criteria = question.resolution_criteria or ""
    user_prompt = f"""
Forecast this binary question using only the information below. Do not browse,
do not call tools, and do not assume access to resolution data after the snapshot.

Question ID: {question.id}
Snapshot time: {snapshot_time}
Title: {question.title}
Description: {content}
Resolution criteria: {criteria}

Return exactly one JSON object with this schema:
{{
  "probability": <number from 0 to 1>,
  "reasoning": <concise explanation>,
  "logical_trace": [
    {{"event": <key assumption>, "probability": <number from 0 to 1>, "description": <why it matters>}}
  ],
  "structural_trace": ["load_question", "local_llm_forecast", "validate_output"]
}}
""".strip()
    return [
        {
            "role": "system",
            "content": "You are a calibrated forecasting engine. Output valid JSON only.",
        },
        {"role": "user", "content": user_prompt},
    ]


def parse_llm_forecast_payload(text: str) -> dict[str, Any]:
    r"""Parse model text into a forecast payload, tolerating Qwen reasoning tags.

    Qwen reasoning models may prepend ``<think>...</think>`` blocks or wrap JSON
    in Markdown fences. This parser strips those wrappers and extracts the first
    JSON object without treating hidden reasoning text as structured output.
    """
    cleaned, hidden_reasoning = _strip_qwen_reasoning(text)
    parsed = _parse_first_json_object(cleaned)
    if hidden_reasoning and "qwen_reasoning" not in parsed:
        parsed["qwen_reasoning"] = hidden_reasoning
    return parsed


def run_real_question_e2e(
    *,
    limit: int = 2,
    provider: Optional[InferenceProvider] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    max_tokens: int = 768,
    temperature: float = 0.0,
    artifact_dir: Optional[Path] = None,
    write_artifacts: bool = True,
) -> list[ForecastHarnessRecord]:
    r"""Run a bounded deterministic-corpus forecast pass against a local LLM."""
    if limit < 1:
        raise ValueError("limit must be at least 1")

    active_provider = provider or _build_local_openai_provider(base_url=base_url, model=model, api_key=api_key)
    questions = load_real_binary_questions(limit=limit)
    records: list[ForecastHarnessRecord] = []
    for question in questions:
        prompt = build_real_question_prompt(question)
        response, output = _generate_valid_forecast_output(
            question=question,
            provider=active_provider,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        validate_forecast_output_integrity(question, output)
        records.append(
            ForecastHarnessRecord(
                question_id=question.id,
                output=output,
                provider_metadata={
                    "model": getattr(active_provider, "model_id", model),
                    "base_url": str(getattr(active_provider, "base_url", base_url)),
                    "usage": dict(response.usage),
                    "response_metadata": dict(response.metadata),
                },
            )
        )

    if write_artifacts:
        _write_records(records, artifact_dir or default_artifact_dir())
    return records


def validate_forecast_output_integrity(question: ForecastQuestion, output: ForecastOutput) -> None:
    r"""Validate harness output integrity and audit-field usability."""
    errors: list[str] = []
    if output.question_id != question.id:
        errors.append(f"question_id mismatch: {output.question_id!r} != {question.id!r}")
    if not 0 <= output.probability <= 1:
        errors.append(f"probability out of bounds: {output.probability}")
    if not output.reasoning.strip():
        errors.append("reasoning is empty")
    if output.metadata.created_at is None:
        errors.append("metadata.created_at is missing")
    if output.metadata.snapshot_time is None:
        errors.append("metadata.snapshot_time is missing")
    if not output.logical_trace:
        errors.append("logical_trace is empty")
    if not output.structural_trace:
        errors.append("structural_trace is empty")

    reasoning_trace = output.reasoning_trace
    if not isinstance(reasoning_trace.get("narrative"), str) or not reasoning_trace["narrative"].strip():
        errors.append("reasoning_trace narrative is unusable")
    causal_graph = reasoning_trace.get("causal_graph")
    if not isinstance(causal_graph, dict) or not isinstance(causal_graph.get("nodes"), list):
        errors.append("reasoning_trace causal graph nodes are unusable")

    output.model_dump(mode="json")
    try:
        graph = output.to_networkx()
        if graph.number_of_nodes() < 1:
            errors.append("logical_trace graph has no nodes")
    except Exception as exc:  # pragma: no cover - defensive around optional graph backends
        errors.append(f"logical_trace graph is unusable: {exc}")

    if errors:
        raise ForecastOutputValidationError("; ".join(errors))


def _build_local_openai_provider(
    *, base_url: Optional[str], model: Optional[str], api_key: Optional[str]
) -> InferenceProvider:
    model_id = model or os.environ.get("XRTM_LOCAL_LLM_MODEL") or "Qwen3.5-27B-Q4_K_M.gguf"
    api_key_value = api_key or os.environ.get("XRTM_LOCAL_LLM_API_KEY") or "test"
    base_url_value = base_url or os.environ.get("XRTM_LOCAL_LLM_BASE_URL") or "http://localhost:8080/v1"
    config = OpenAIConfig(
        model_id=model_id,
        api_key=SecretStr(api_key_value),
        base_url=base_url_value.rstrip("/"),
    )
    return ModelFactory.get_provider(config)


def _generate_valid_forecast_output(
    *,
    question: ForecastQuestion,
    provider: InferenceProvider,
    prompt: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> tuple[ModelResponse, ForecastOutput]:
    token_budgets = _structured_output_token_budgets(max_tokens)
    for attempt_index, token_budget in enumerate(token_budgets):
        response = provider.generate_content(
            prompt,
            max_tokens=token_budget,
            temperature=temperature,
        )
        try:
            return response, _build_output_from_response(question, response, provider)
        except ValueError as exc:
            if not _is_missing_json_error(exc) or attempt_index == len(token_budgets) - 1:
                raise
    raise ValueError("model response did not contain a JSON object")


def _build_output_from_response(
    question: ForecastQuestion,
    response: ModelResponse,
    provider: InferenceProvider,
) -> ForecastOutput:
    raw_text, raw_reasoning = _response_text_and_reasoning(response)
    payload = _parse_response_forecast_payload(raw_text, raw_reasoning)
    probability = _coerce_probability(payload.get("probability", payload.get("confidence")))
    reasoning = _coerce_reasoning(payload, raw_reasoning)
    logical_trace = _coerce_logical_trace(_trace_nodes_payload(payload), probability, reasoning, question.id)
    structural_trace = _coerce_string_list(
        payload.get("structural_trace"),
        default=["load_question", "local_llm_forecast", "validate_output"],
    )
    return ForecastOutput(
        question_id=question.id,
        probability=probability,
        reasoning=reasoning,
        logical_trace=logical_trace,
        structural_trace=structural_trace,
        metadata=MetadataBase(
            snapshot_time=question.metadata.snapshot_time,
            tags=sorted({*question.metadata.tags, "real-question-e2e", "local-llm"}),
            subject_type="binary",
            source_version=REAL_BINARY_CORPUS_ID,
            raw_data={
                "corpus_id": REAL_BINARY_CORPUS_ID,
                "provider_model": getattr(provider, "model_id", None),
                "usage": dict(response.usage),
                "qwen_reasoning_present": bool(payload.get("qwen_reasoning") or raw_reasoning),
            },
        ),
    )



def _parse_response_forecast_payload(raw_text: str, raw_reasoning: str) -> dict[str, Any]:
    errors: list[Exception] = []
    for candidate in (raw_text, raw_reasoning):
        if not candidate.strip():
            continue
        try:
            return parse_llm_forecast_payload(candidate)
        except ValueError as exc:
            errors.append(exc)
    if errors:
        raise errors[-1]
    raise ValueError("model response did not contain a JSON object")


def _is_missing_json_error(exc: ValueError) -> bool:
    return "JSON object" in str(exc)


def _structured_output_token_budgets(max_tokens: int) -> list[int]:
    budgets = [max_tokens, max(2048, max_tokens * 2), max(4096, max_tokens * 4)]
    return list(dict.fromkeys(budgets))


def _strip_qwen_reasoning(text: str) -> tuple[str, str]:
    reasoning_parts = [match.group(1).strip() for match in _THINK_BLOCK_RE.finditer(text) if match.group(1).strip()]
    cleaned = _THINK_BLOCK_RE.sub("", text).strip()
    return cleaned, "\n\n".join(reasoning_parts)


def _parse_first_json_object(text: str) -> dict[str, Any]:
    candidates = [match.group(1).strip() for match in _FENCE_RE.finditer(text)]
    candidates.append(text.strip())
    decoder = json.JSONDecoder()
    for candidate in candidates:
        for start in [index for index, char in enumerate(candidate) if char == "{"]:
            try:
                parsed, _ = decoder.raw_decode(candidate[start:])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
    raise ValueError("model response did not contain a JSON object")


def _coerce_probability(value: Any) -> float:
    if value is None:
        raise ValueError("forecast payload is missing probability")
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.endswith("%"):
            return float(stripped[:-1].strip()) / 100.0
        return float(stripped)
    return float(value)


def _coerce_reasoning(payload: dict[str, Any], raw_reasoning: str) -> str:
    reasoning = payload.get("reasoning") or payload.get("rationale") or payload.get("explanation")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()

    reasoning_trace = payload.get("reasoning_trace")
    if isinstance(reasoning_trace, dict):
        narrative = reasoning_trace.get("narrative")
        if isinstance(narrative, str) and narrative.strip():
            return narrative.strip()

    if raw_reasoning.strip():
        return raw_reasoning.strip()
    raise ValueError("forecast payload is missing reasoning")


def _trace_nodes_payload(payload: dict[str, Any]) -> Any:
    if "logical_trace" in payload:
        return payload["logical_trace"]
    reasoning_trace = payload.get("reasoning_trace")
    if isinstance(reasoning_trace, dict):
        causal_graph = reasoning_trace.get("causal_graph")
        if isinstance(causal_graph, dict) and "nodes" in causal_graph:
            return causal_graph["nodes"]
    return None


def _coerce_logical_trace(value: Any, probability: float, reasoning: str, question_id: str) -> list[CausalNode]:
    nodes: list[CausalNode] = []
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        for index, item in enumerate(value):
            if isinstance(item, CausalNode):
                nodes.append(item)
            elif isinstance(item, dict):
                item_data = dict(item)
                item_data.setdefault("node_id", f"{question_id}:llm:{index}")
                item_data.setdefault("event", item_data.get("description", f"assumption_{index}"))
                nodes.append(CausalNode.model_validate(item_data))
            elif isinstance(item, str) and item.strip():
                nodes.append(
                    CausalNode(
                        node_id=f"{question_id}:llm:{index}",
                        event=item.strip(),
                        probability=probability,
                        description=item.strip(),
                    )
                )
    if nodes:
        return nodes
    return [
        CausalNode(
            node_id=f"{question_id}:llm:summary",
            event="local_llm_forecast",
            probability=probability,
            description=reasoning,
        )
    ]


def _coerce_string_list(value: Any, *, default: list[str]) -> list[str]:
    if isinstance(value, list):
        strings = [str(item).strip() for item in value if str(item).strip()]
        if strings:
            return strings
    return default


def _response_text_and_reasoning(response: ModelResponse) -> tuple[str, str]:
    raw_reasoning = ""
    try:
        message = response.raw.choices[0].message
        for attr in ("reasoning_content", "reasoning"):
            value = getattr(message, attr, None)
            if isinstance(value, str) and value.strip():
                raw_reasoning = value.strip()
                break
    except (AttributeError, IndexError, TypeError):
        pass
    return response.text or "", raw_reasoning


def _write_records(records: list[ForecastHarnessRecord], artifact_dir: Path) -> Path:
    _ensure_ignored_artifact_path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact_path = artifact_dir / f"real-question-e2e-{timestamp}.jsonl"
    with artifact_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")
    return artifact_path


def _ensure_ignored_artifact_path(path: Path) -> None:
    if path.is_absolute():
        try:
            path = path.relative_to(Path.cwd())
        except ValueError as exc:
            raise ValueError("artifact_dir must be under the current workspace") from exc
    parts = path.parts
    if not parts or parts[0] not in _ALLOWED_ARTIFACT_ROOTS:
        allowed = ", ".join(sorted(_ALLOWED_ARTIFACT_ROOTS))
        raise ValueError(f"artifact_dir must be under an ignored runtime directory ({allowed})")
