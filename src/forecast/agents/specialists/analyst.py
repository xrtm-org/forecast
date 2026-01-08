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
from typing import List, Union

from pydantic import BaseModel, Field

from forecast.agents.llm import LLMAgent
from forecast.schemas.forecast import CausalNode, ForecastOutput, ForecastQuestion

logger = logging.getLogger(__name__)


class AnalystOutput(BaseModel):
    r"""
    Internal schema for structured output from the Forecasting Analyst.
    """

    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
    causal_chain: List[CausalNode] = Field(default_factory=list)


class ForecastingAnalyst(LLMAgent):
    r"""
    A specialized agent designed for probabilistic forecasting and event analysis.

    The `ForecastingAnalyst` acts as a domain-agnostic reasoning engine. It can
    automatically leverage available skills (like `WebSearchSkill`) to gather
    evidence before producing a structured forecast with a causal reasoning trace.

    Note: This is a **Reference Implementation**. Domain experts are encouraged
    to fork and customize the persona, few-shot examples, and structural constraints
    for specific forecasting niches.
    """

    async def run(self, input_data: Union[str, ForecastQuestion], **kwargs) -> ForecastOutput:
        """
        Processes a ForecastQuestion (or a raw string) and returns a ForecastOutput.
        Demonstrates how to use skills if they are present.
        """
        if isinstance(input_data, str):
            input_data = ForecastQuestion(
                id="quick-query",
                title=input_data,
                content="Auto-generated from string input.",
            )

        context = input_data.content or "No additional context provided."

        # Dynamic Skill Usage: If the agent has a 'web_search' skill, use it to gather more info.
        search_skill = self.get_skill("web_search")
        if search_skill:
            logger.info(f"Analyst '{self.name}' is using web_search skill...")
            skill_result = await search_skill.execute(query=input_data.title)
            context = f"{context}\n\nSearch Findings:\n{skill_result}"

        prompt = f"""
        Analyze the following event and provide a probabilistic forecast:
        Title: {input_data.title}
        Context: {context}

        Provide your response in JSON format matching this schema:
        - confidence: (float 0-1)
        - reasoning: (narrative text)
        - causal_chain: (list of {{'event': string, 'probability': float, 'description': string}})
        """

        response = await self.model.generate_content_async(prompt)
        parsed = self.parse_output(response.text, schema=AnalystOutput)

        # Type guard for Mypy
        confidence = 0.5
        reasoning = "Parsing failed."
        logical_trace = []

        if isinstance(parsed, AnalystOutput):
            confidence = parsed.confidence
            reasoning = parsed.reasoning
            logical_trace = parsed.causal_chain
        elif isinstance(parsed, dict):
            confidence = parsed.get("confidence", 0.5)
            reasoning = parsed.get("reasoning", "Parsing failed fallback.")
            logical_trace = parsed.get("causal_chain", [])

        # Wrap the parsed output into the standardized ForecastOutput
        return ForecastOutput(
            question_id=input_data.id,
            confidence=confidence,
            reasoning=reasoning,
            logical_trace=logical_trace,
            metadata={
                "model_id": getattr(self.model, "model_id", "unknown"),
                "token_usage": getattr(response, "usage", {}),
            },
        )


__all__ = ["ForecastingAnalyst"]
