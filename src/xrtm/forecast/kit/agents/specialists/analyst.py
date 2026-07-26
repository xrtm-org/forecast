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

from xrtm.forecast.core.schemas.forecast import CausalEdge, CausalNode, ForecastOutput, ForecastQuestion, MetadataBase
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
    ):
        super().__init__(model=model, name=name)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.few_shot_examples = few_shot_examples or []

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

        response = await self.model.generate_content_async(prompt, **gen_kwargs)
        parsed = self.parse_output(response.text, schema=AnalystOutput)

        # Defaults for safe fallback
        probability = 0.5
        confidence_interval = _default_confidence_interval(probability)
        reasoning = "Parsing failed."
        nodes = []
        edges = []

        if isinstance(parsed, AnalystOutput):
            probability = parsed.probability
            confidence_interval = parsed.confidence_interval
            reasoning = parsed.reasoning
            nodes = [CausalNode(**n) for n in parsed.causal_nodes]
            edges = [_sanitize_edge(e) for e in parsed.causal_edges]
        elif isinstance(parsed, dict):
            probability = parsed.get("probability", 0.5)
            confidence_interval = parsed.get("confidence_interval", _default_confidence_interval(probability))
            reasoning = parsed.get("reasoning", "Parsing failed fallback.")
            nodes = [CausalNode(**n) for n in parsed.get("causal_nodes", [])]
            edges = [_sanitize_edge(e) for e in parsed.get("causal_edges", [])]

        # Build raw_data with token usage and optional search metadata
        raw_data: dict[str, Any] = {"token_usage": getattr(response, "usage", {})}
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
            metadata=MetadataBase(
                source_version=getattr(self.model, "model_id", "unknown"),
                raw_data=raw_data,
            ),
        )


__all__ = ["ForecastingAnalyst"]
