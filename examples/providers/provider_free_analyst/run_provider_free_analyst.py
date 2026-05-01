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
Provider-Free Analyst Example
Demonstrates using the DeterministicProvider for testing and learning.
"""

import asyncio

from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from xrtm.product.providers import DeterministicProvider


async def main():
    """
    Run the ForecastingAnalyst with a provider-free backend.
    
    This example shows how to test and learn XRTM without API keys.
    The DeterministicProvider returns structured, deterministic forecasts
    without making any network calls.
    """
    # Create provider-free model
    provider = DeterministicProvider()
    
    # Create agent with provider-free backend
    agent = ForecastingAnalyst(model=provider)
    
    print("--- Provider-Free Forecasting Analyst ---")
    print(f"Model: {provider.model_id}")
    print(f"Base URL: {provider.base_url}")
    print()
    
    # Run forecasts
    questions = [
        "Will the S&P 500 close above 5,000 by end of 2026?",
        "Will inflation exceed 3% in 2026?",
        "Will AGI be announced before 2030?",
    ]
    
    for question in questions:
        result = await agent.run(question)
        print(f"Question: {question}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Reasoning: {result.reasoning[:100]}...")
        print()
    
    # Inspect cache
    cache = provider.cache_snapshot
    print("--- Cache Statistics ---")
    print(f"Hits: {cache['hits']}")
    print(f"Misses: {cache['misses']}")
    print(f"Hit rate: {cache['hit_rate']:.2%}")
    print(f"Entries: {cache['entries']}")


if __name__ == "__main__":
    asyncio.run(main())
