"""
Minimal Agent Example (v0.1.2)
Showcasing explicit configuration and user-defined model defaults.
"""

import asyncio
import os

from pydantic import SecretStr

from forecast.agents.specialists.analyst import ForecastingAnalyst
from forecast.inference.config import GeminiConfig
from forecast.inference.factory import ModelFactory

# In actual user applications, you define your preferred models and tiers here.
# The core platform remains abstract and model-agnostic.
DEFAULT_MODEL = "gemini-2.0-flash"

async def main():
    # 1. Load API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Please set GEMINI_API_KEY environment variable.")
        return

    # 2. Explicitly configure the model
    config = GeminiConfig(
        model_id=DEFAULT_MODEL,
        api_key=SecretStr(api_key)
    )

    # 3. Create the agent with the explicit model
    model = ModelFactory.get_provider(config)
    agent = ForecastingAnalyst(model=model)

    print(f"--- Running Forecasting Analyst: {agent.name} ({DEFAULT_MODEL}) ---")

    # We can pass a raw string or a structured ForecastQuestion
    result = await agent.run("Will the S&P 500 close above 5,000 by end of 2026?")

    print(f"\nConfidence: {result.confidence * 100:.1f}%")
    print(f"Reasoning: {result.reasoning[:300]}...")


if __name__ == "__main__":
    asyncio.run(main())
