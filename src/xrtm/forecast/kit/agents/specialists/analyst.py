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

r"""Domain analyst specialist agent.

A pre-configured agent specialized in deep-dive analysis of a
specific subject, combining web research, data retrieval, and
structured reasoning into a coherent analytical output.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator
from xrtm.data.core.schemas.forecast import (
    CausalEdge,
    CausalNode,
    ForecastOutput,
    ForecastProvenance,
    ForecastQuestion,
    MetadataBase,
    TokenUsage,
)

from xrtm.forecast.core.exceptions import ForecastParseError
from xrtm.forecast.core.utils.parser import parse_json_markdown
from xrtm.forecast.core.utils.schemas import json_object_response_format
from xrtm.forecast.kit.agents.llm import LLMAgent

logger = logging.getLogger(__name__)


def _default_confidence_interval(probability: float = 0.5) -> Dict[str, float]:
    r"""Synthesize a bounded confidence interval for legacy payloads."""

    center = min(max(float(probability), 0.0), 1.0)
    return {
        "low": round(max(0.0, center - 0.1), 3),
        "high": round(min(1.0, center + 0.1), 3),
        "level": 0.9,
    }


def _sanitize_edge(edge_data: Dict[str, Any]) -> CausalEdge:
    r"""Coerce edge weight to [0, 1] range, taking abs for negative weights."""
    data = dict(edge_data)
    if "weight" in data:
        data["weight"] = max(0.0, min(1.0, abs(float(data["weight"]))))
    return CausalEdge(**data)


class AnalystOutput(BaseModel):
    r"""
    Internal schema for structured output from the Forecasting Analyst.
    """

    probability: float = Field(..., ge=0, le=1)
    confidence_interval: Dict[str, float] = Field(
        ..., description="Map containing 'low', 'high', and 'level' (e.g., 0.9)"
    )
    reasoning: str
    causal_nodes: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of reasoning steps with 'node_id' and 'event'"
    )
    causal_edges: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of directed dependencies with 'source' and 'target'"
    )

    @model_validator(mode="before")
    @classmethod
    def _backfill_confidence_interval(cls, data: Any) -> Any:
        r"""Accept legacy analyst payloads that omitted `confidence_interval`."""
        if not isinstance(data, dict):
            return data

        updated = dict(data)
        if "confidence_interval" not in updated:
            updated["confidence_interval"] = _default_confidence_interval(updated.get("probability", 0.5))
        return updated


class ForecastingAnalyst(LLMAgent):
    r"""
    A specialized agent designed for probabilistic forecasting and event analysis.

    The `ForecastingAnalyst` acts as a domain-agnostic reasoning engine. It can
    automatically leverage available skills (like `WebSearchSkill`) to gather
    evidence before producing a structured forecast with a causal reasoning trace.

    Args:
        model: The inference provider for LLM calls.
        name: Logical name for the agent.
        temperature: Temperature for LLM generation (default None — uses provider default).
        max_tokens: Max tokens for LLM generation (default None — uses provider default).
        system_prompt: Optional custom system prompt. If None, uses the default.
        few_shot_examples: Optional list of few-shot example strings injected into the prompt.
        structured_output: Request provider-enforced JSON output (``response_format``).
        prompt_id: Identifier recorded in the forecast provenance (prompt-template version).
        strict_parse: When True, raise :class:`ForecastParseError` instead of returning
            a flagged fallback forecast if parsing fails.

    Note: This is a **Reference Implementation**. Domain experts are encouraged
    to fork and customize the persona, few-shot examples, and structural constraints
    for specific forecasting niches.
    r"""

    def __init__(
        self,
        model: Any,
        name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        few_shot_examples: Optional[List[str]] = None,
        structured_output: bool = False,
        prompt_id: str = "analyst-default",
        strict_parse: bool = False,
    ):
        super().__init__(model=model, name=name)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.few_shot_examples = few_shot_examples or []
        self.structured_output = structured_output
        self.prompt_id = prompt_id
        self.strict_parse = strict_parse

    async def run(self, input_data: Union[str, ForecastQuestion], **kwargs: Any) -> ForecastOutput:
        r"""
        Processes a ForecastQuestion (or a raw string) and returns a ForecastOutput.
        Demonstrates how to use skills if they are present.
        r"""
        if isinstance(input_data, str):
            input_data = ForecastQuestion(
                id="quick-query",
                title=input_data,
                description="Auto-generated from string input.",
            )

        context_parts = [input_data.description or "No additional context provided."]

        # Merge optional question.context (market metadata, etc.)
        question_context = getattr(input_data, "context", None)
        if question_context:
            context_items = [f"{k}: {v}" for k, v in question_context.items()]
            context_parts.append("Market Context:\n" + "\n".join(context_items))

        context = "\n\n".join(context_parts)
        search_metadata: dict[str, Any] | None = None

        # Dynamic Skill Usage: If the agent has a 'web_search' skill, use it to gather more info.
        search_skill = self.get_skill("web_search")
        if search_skill:
            logger.info(f"Analyst '{self.name}' is using web_search skill...")
            skill_result = await search_skill.execute(query=input_data.title)
            if isinstance(skill_result, dict):
                # Structured return from WebSearchSkill
                context = f"{context}\n\nSearch Findings:\n{skill_result['formatted']}"
                search_metadata = {
                    "web_search": {
                        "query": skill_result["query"],
                        "results_count": skill_result["results_count"],
                        "sources": skill_result["sources"],
                        "search_time_ms": skill_result["search_time_ms"],
                    }
                }
            else:
                # Legacy string return
                context = f"{context}\n\nSearch Findings:\n{skill_result}"

        # Build the system prompt
        default_system = (
            "Analyze the following event and provide a probabilistic forecast "
            "according to xrtm Governance v1."
        )
        system_text = self.system_prompt or default_system

        # Build few-shot section
        few_shot_text = ""
        if self.few_shot_examples:
            few_shot_text = "\n\nExamples:\n" + "\n---\n".join(self.few_shot_examples)

        prompt = f"""
        {system_text}
        Title: {input_data.title}
        Context: {context}
        {few_shot_text}

        Provide your response in JSON format matching this schema:
        - probability: (float 0-1)
        - confidence_interval: {{'low': float, 'high': float, 'level': 0.9}}
        - reasoning: (narrative text)
        - causal_nodes: (list of {{'node_id': string, 'event': string, 'probability': float, 'description': string}})
        - causal_edges: (list of {{'source': string, 'target': string, 'weight': float}})

        Ensure the causal_nodes and causal_edges form a valid Directed Acyclic Graph (DAG) representing your reasoning.
        """

        # Build generation kwargs
        gen_kwargs: dict[str, Any] = {}
        if self.temperature is not None:
            gen_kwargs["temperature"] = self.temperature
        if self.max_tokens is not None:
            gen_kwargs["max_tokens"] = self.max_tokens
        if self.structured_output:
            gen_kwargs["response_format"] = json_object_response_format()

        response = await self.model.generate_content_async(prompt, **gen_kwargs)

        # --- Parse with explicit status -------------------------------------
        raw_text = getattr(response, "text", "") or ""
        parsed_payload: Optional[Dict[str, Any]] = None
        parse_status = "ok"

        if not raw_text.strip():
            parse_status = "empty_content"
        else:
            candidate = parse_json_markdown(raw_text)
            if candidate is None:
                parse_status = "invalid_json"
            elif not isinstance(candidate, dict):
                parse_status = "schema_error"
            else:
                parsed_payload = candidate

        analyst_output: Optional[AnalystOutput] = None
        if parsed_payload is not None:
            try:
                valid_fields = AnalystOutput.model_fields.keys()
                filtered = {k: v for k, v in parsed_payload.items() if k in valid_fields}
                analyst_output = AnalystOutput(**filtered)
            except Exception:
                parse_status = "schema_error"

        if parse_status != "ok" and self.strict_parse:
            raise ForecastParseError(
                f"Structured forecast parsing failed for prompt '{self.prompt_id}' "
                f"(status={parse_status}): {raw_text[:200]!r}"
            )

        # Defaults for safe fallback (explicitly flagged via parse_status)
        probability = 0.5
        confidence_interval = _default_confidence_interval(probability)
        reasoning = "Parsing failed." if parse_status != "ok" else "Parsing returned no payload."
        nodes: List[CausalNode] = []
        edges: List[CausalEdge] = []

        if analyst_output is not None:
            probability = analyst_output.probability
            confidence_interval = analyst_output.confidence_interval
            reasoning = analyst_output.reasoning
            nodes = [CausalNode(**n) for n in analyst_output.causal_nodes]
            edges = [_sanitize_edge(e) for e in analyst_output.causal_edges]
        elif parsed_payload is not None:
            probability = float(parsed_payload.get("probability", 0.5) or 0.5)
            confidence_interval = parsed_payload.get("confidence_interval", _default_confidence_interval(probability))
            reasoning = str(parsed_payload.get("reasoning", "Parsing failed fallback."))
            nodes = [CausalNode(**n) for n in parsed_payload.get("causal_nodes", [])]
            edges = [_sanitize_edge(e) for e in parsed_payload.get("causal_edges", [])]

        # --- Telemetry ------------------------------------------------------
        raw_usage: Dict[str, Any] = getattr(response, "usage", None) or {}
        usage = TokenUsage(
            prompt_tokens=int(raw_usage.get("prompt_tokens", 0) or 0),
            completion_tokens=int(raw_usage.get("completion_tokens", 0) or 0),
            cached_prompt_tokens=int(raw_usage.get("cached_prompt_tokens", 0) or 0),
            reasoning_tokens=int(raw_usage.get("reasoning_tokens", 0) or 0),
            total_tokens=int(raw_usage.get("total_tokens", 0) or 0),
        )

        provider_cfg = getattr(self.model, "config", None)
        thinking_mode = getattr(provider_cfg, "thinking", None)
        thinking: Optional[bool] = None
        if thinking_mode == "enabled":
            thinking = True
        elif thinking_mode == "disabled":
            thinking = False

        response_metadata: Dict[str, Any] = getattr(response, "metadata", None) or {}
        provenance = ForecastProvenance(
            provider=type(self.model).__name__,
            model_id=getattr(self.model, "model_id", None),
            prompt_id=self.prompt_id,
            temperature=self.temperature,
            thinking=thinking,
            cache_hit=bool(response_metadata.get("cache_hit", False)),
        )

        # Build raw_data with token usage (legacy surface) and optional search metadata
        raw_data: dict[str, Any] = {"token_usage": raw_usage}
        if response_metadata.get("reasoning_content"):
            raw_data["reasoning_content"] = response_metadata["reasoning_content"]
        if search_metadata:
            raw_data.update(search_metadata)

        # Wrap the parsed output into the standardized ForecastOutput
        return ForecastOutput(
            question_id=input_data.id,
            probability=probability,
            confidence_interval=confidence_interval,  # type: ignore
            reasoning=reasoning,
            logical_trace=nodes,
            logical_edges=edges,
            parse_status=parse_status,
            usage=usage,
            provenance=provenance,
            metadata=MetadataBase(
                source_version=getattr(self.model, "model_id", "unknown"),
                raw_data=raw_data,
            ),
        )


__all__ = ["ForecastingAnalyst"]
