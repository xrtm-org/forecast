import logging
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from forecast.agents.llm import LLMAgent
from forecast.schemas.forecast import ForecastQuestion, ForecastOutput, CausalNode

logger = logging.getLogger(__name__)

class AnalystOutput(BaseModel):
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
    causal_chain: List[CausalNode] = Field(default_factory=list)

class ForecastingAnalyst(LLMAgent):
    """
    Agent specialized in analyzing events and providing probabilistic forecasts.
    Domain-agnostic reasoning engine.
    """
    async def run(self, input_data: ForecastQuestion, **kwargs) -> ForecastOutput:
        """
        Processes a ForecastQuestion and returns a ForecastOutput.
        """
        prompt = f"""
        Analyze the following event and provide a probabilistic forecast:
        Title: {input_data.title}
        Context: {input_data.content or 'No additional context provided.'}
        
        Provide your response in JSON format matching this schema:
        - confidence: (float 0-1)
        - reasoning: (narrative text)
        - causal_chain: (list of {{'event': string, 'probability': float, 'description': string}})
        """
        
        response = await self.model.generate_content_async(prompt)
        parsed = self.parse_output(response.text, schema=AnalystOutput)
        
        # Wrap the parsed output into the standardized ForecastOutput
        return ForecastOutput(
            question_id=input_data.id,
            confidence=parsed.confidence,
            reasoning=parsed.reasoning,
            logical_trace=parsed.causal_chain,
            metadata={
                "model_id": getattr(self.model, "model_id", "unknown"),
                "token_usage": getattr(response, "usage", {})
            }
        )
