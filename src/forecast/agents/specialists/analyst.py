import logging
from typing import List

from pydantic import BaseModel, Field

from forecast.agents.llm import LLMAgent
from forecast.schemas.forecast import CausalNode, ForecastOutput, ForecastQuestion

logger = logging.getLogger(__name__)

class AnalystOutput(BaseModel):
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
    causal_chain: List[CausalNode] = Field(default_factory=list)

class ForecastingAnalyst(LLMAgent):
    """
    Agent specialized in analyzing events and providing probabilistic forecasts.
    Domain-agnostic reasoning engine.

    Note: This is a Reference Implementation (Recipe). Users are encouraged to
    fork and customize this persona for specific domains.
    """
    async def run(self, input_data: ForecastQuestion, **kwargs) -> ForecastOutput:
        """
        Processes a ForecastQuestion and returns a ForecastOutput.
        Demonstrates how to use skills if they are present.
        """
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
                "token_usage": getattr(response, "usage", {})
            }
        )
