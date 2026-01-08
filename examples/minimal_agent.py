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
Quickstart Example (v0.1.2)
Showcasing zero-boilerplate agent instantiation using factories.
"""

import asyncio

from forecast.agents.specialists.analyst import ForecastingAnalyst
from forecast.schemas.forecast import ForecastQuestion


async def main():
    # Phase 2: Zero-boilerplate instantiation
    # Automatically loads API keys and model settings from environment
    agent = ForecastingAnalyst.from_config()

    question = ForecastQuestion(
        question_id="quickstart-1",
        title="Will the S&P 500 close above 5,000 by end of 2026?",
        description="Analysis of US market trends and economic indicators.",
        deadline="2026-12-31T23:59:59Z",
    )

    print(f"--- Running Forecasting Analyst: {agent.name} ---")
    result = await agent.run(question)

    print(f"\nConfidence: {result.confidence * 100:.1f}%")
    print(f"Reasoning: {result.reasoning[:200]}...")


if __name__ == "__main__":
    asyncio.run(main())
