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

"""
Minimal Agent Example (v0.2.1)
Showcasing explicit configuration and user-defined model defaults.
"""

import asyncio

from forecast.core.config.inference import GeminiConfig
from forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from forecast.providers.inference.factory import ModelFactory

# In actual user applications, you define your preferred models and tiers here.
# The core platform remains abstract and model-agnostic.
DEFAULT_MODEL = "gemini-2.0-flash"


async def main():
    # 1. Explicitly configure the model
    # Note: API keys are automatically injected from environment if not provided here.
    config = GeminiConfig(model_id=DEFAULT_MODEL)

    # 2. Create the agent with the explicit model
    model = ModelFactory.get_provider(config)
    agent = ForecastingAnalyst(model=model)

    print(f"--- Running Forecasting Analyst: {agent.name} ({DEFAULT_MODEL}) ---")

    # We can pass a raw string or a structured ForecastQuestion
    result = await agent.run("Will the S&P 500 close above 5,000 by end of 2026?")

    print(f"\nConfidence: {result.confidence}")
    print(f"Reasoning: {result.reasoning[:300]}...")


if __name__ == "__main__":
    asyncio.run(main())
