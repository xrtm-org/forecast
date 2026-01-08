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

import asyncio
import logging
import os
from typing import Callable

from pydantic import BaseModel, Field, SecretStr

from forecast import (
    BaseGraphState,
    LLMAgent,
    ModelFactory,
    Orchestrator,
    ToolAgent,
)
from forecast.inference.config import GeminiConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("custom-showcase")


# 1. Custom Data Schema for this specific mission
class SentimentResult(BaseModel):
    r"""
    Data model for sentiment analysis output.
    """

    sentiment: str = Field(..., description="The detected sentiment (BULLISH/BEARISH/NEUTRAL)")
    confidence: float = Field(..., ge=0, le=1)
    explanation: str


# 2. Custom Specialized Agents
class SentimentAgent(LLMAgent):
    """Analyzes text for directional sentiment using an LLM."""

    async def run(self, input_data: str, **kwargs) -> SentimentResult:
        """
        Custom run method.
        """
        prompt = f"Analyze the sentiment of this text: {input_data}"
        response = await self.model.generate_content_async(prompt)
        parsed = self.parse_output(response.text, schema=SentimentResult)
        if isinstance(parsed, SentimentResult):
            return parsed
        # Fallback
        return SentimentResult(sentiment="NEUTRAL", confidence=0.0, explanation="Failed to parse")


def get_trend_multiplier(sentiment: str) -> float:
    """A deterministic tool to calculate a trend multiplier."""
    mapping = {"BULLISH": 1.2, "NEUTRAL": 1.0, "BEARISH": 0.8}
    return mapping.get(sentiment, 1.0)


# 3. Custom Node Functions (The 'Lego' assembly)
async def fetch_news_node(state: BaseGraphState, on_progress: Callable) -> str:
    await on_progress(1, "Data", "PROCESSING", f"Fetching news for {state.subject_id}")
    # In a real app, this would be an API call
    state.context["raw_news"] = (
        f"Recent technological breakthroughs in {state.subject_id} are driving massive investor interest."
    )
    return "analyze"


async def analyze_node(state: BaseGraphState, on_progress: Callable) -> str:
    sentiment_agent = state.context["agents"]["sentiment"]
    await on_progress(2, "Analysis", "PROCESSING", "Running sentiment agent")

    sentiment = await sentiment_agent.run(state.context["raw_news"])
    state.context["sentiment"] = sentiment
    return "calculate_trend"


async def trend_node(state: BaseGraphState, on_progress: Callable) -> str:
    trend_agent = state.context["agents"]["trend_multiplier"]
    await on_progress(3, "Calculation", "PROCESSING", "Calculating trend multiplier")

    sentiment_val = state.context["sentiment"].sentiment
    multiplier = await trend_agent.run(sentiment_val)
    state.context["multiplier"] = multiplier
    return "final_report"


async def report_node(state: BaseGraphState, on_progress: Callable) -> None:
    sentiment = state.context["sentiment"]
    multiplier = state.context["multiplier"]

    print("\n" + "=" * 40)
    print("--- ADVANCED CUSTOM REPORT ---")
    print(f"Subject: {state.subject_id}")
    print(f"Detected Sentiment: {sentiment.sentiment} ({sentiment.confidence * 100:.1f}%)")
    print(f"Trend Multiplier: {multiplier}x")
    print(f"Explanation: {sentiment.explanation}")
    print("=" * 40 + "\n")
    return None


# 4. Assembling the Custom Pipeline
async def run_custom_pipeline():
    r"""
    Executes a custom multi-agent sentiment analysis workflow.
    """
    # Setup Inference
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found. Skipping execution.")
        return

    config = GeminiConfig(
        model_id="gemini-2.0-flash-lite",
        api_key=SecretStr(api_key),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )
    model = ModelFactory.get_provider(config)

    # Initialize Agents
    sentiment_agent = SentimentAgent(model=model, name="Sentiment")
    trend_tool = ToolAgent(fn=get_trend_multiplier, name="TrendMultiplier")

    # Orchestrator
    from forecast.graph.config import GraphConfig

    orchestrator = Orchestrator(config=GraphConfig(max_cycles=10))
    orchestrator.register_node("fetch_news", fetch_news_node)
    orchestrator.register_node("analyze", analyze_node)
    orchestrator.register_node("calculate_trend", trend_node)
    orchestrator.register_node("final_report", report_node)

    state = BaseGraphState(subject_id="Nuclear Fusion")
    state.context["agents"] = {"sentiment": sentiment_agent, "trend_multiplier": trend_tool}

    print(">>> Starting Advanced Custom Pipeline (Institutional Grade)")
    await orchestrator.run(state, entry_node="fetch_news")


if __name__ == "__main__":
    asyncio.run(run_custom_pipeline())
