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

import logging
from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field

from xrtm.forecast.core.schemas.forecast import CausalEdge, CausalNode, ForecastOutput, ForecastQuestion, MetadataBase
from xrtm.forecast.kit.agents.llm import LLMAgent

logger = logging.getLogger(__name__)


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


class ForecastingAnalyst(LLMAgent):
    r"""
    A specialized agent designed for probabilistic forecasting and event analysis.

    The `ForecastingAnalyst` acts as a domain-agnostic reasoning engine. It can
    automatically leverage available skills (like `WebSearchSkill`) to gather
    evidence before producing a structured forecast with a causal reasoning trace.

    Note: This is a **Reference Implementation**. Domain experts are encouraged
    to fork and customize the persona, few-shot examples, and structural constraints
    for specific forecasting niches.
    r"""

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

        context = input_data.description or "No additional context provided."

        # Dynamic Skill Usage: If the agent has a 'web_search' skill, use it to gather more info.
        search_skill = self.get_skill("web_search")
        if search_skill:
            logger.info(f"Analyst '{self.name}' is using web_search skill...")
            skill_result = await search_skill.execute(query=input_data.title)
            context = f"{context}\n\nSearch Findings:\n{skill_result}"

        prompt = f"""
        Analyze the following event and provide a probabilistic forecast according to xrtm Governance v1:
        Title: {input_data.title}
        Context: {context}

        Provide your response in JSON format matching this schema:
        - probability: (float 0-1)
        - confidence_interval: {{'low': float, 'high': float, 'level': 0.9}}
        - reasoning: (narrative text)
        - causal_nodes: (list of {{'node_id': string, 'event': string, 'probability': float, 'description': string}})
        - causal_edges: (list of {{'source': string, 'target': string, 'weight': float}})

        Ensure the causal_nodes and causal_edges form a valid Directed Acyclic Graph (DAG) representing your reasoning.
        """

        response = await self.model.generate_content_async(prompt)
        parsed = self.parse_output(response.text, schema=AnalystOutput)

        # Defaults for safe fallback
        probability = 0.5
        confidence_interval = {"low": 0.4, "high": 0.6, "level": 0.9}
        reasoning = "Parsing failed."
        nodes = []
        edges = []

        if isinstance(parsed, AnalystOutput):
            probability = parsed.probability
            confidence_interval = parsed.confidence_interval
            reasoning = parsed.reasoning
            nodes = [CausalNode(**n) for n in parsed.causal_nodes]
            edges = [CausalEdge(**e) for e in parsed.causal_edges]
        elif isinstance(parsed, dict):
            probability = parsed.get("probability", 0.5)
            confidence_interval = parsed.get("confidence_interval", confidence_interval)
            reasoning = parsed.get("reasoning", "Parsing failed fallback.")
            nodes = [CausalNode(**n) for n in parsed.get("causal_nodes", [])]
            edges = [CausalEdge(**e) for e in parsed.get("causal_edges", [])]

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
                raw_data={"token_usage": getattr(response, "usage", {})},
            ),
        )


__all__ = ["ForecastingAnalyst"]
