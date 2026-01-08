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
Discovery & Functional Skills Showcase (v0.1.2)
Demonstrating how to define skills succinctly and discover them at runtime.
"""

import asyncio

from forecast.skills.definitions import skill
from forecast.tools.registry import tool_registry


# 1. Define a custom skill with a single decorator
@skill(name="market_sentiment_analyzer")
async def analyze_sentiment(ticker: str):
    """
    Analyzes social and news sentiment for a given stock ticker.
    Returns a score between -1 and 1.
    """
    print(f"[Skill] Analyzing sentiment for {ticker}...")
    # Mock logic
    return 0.75


async def main():
    # 2. Discover available capabilities at runtime
    print("--- Runtime Discovery: Available Capabilities ---")
    available = tool_registry.list_available()

    for item in available:
        first_line = item["description"].strip().split("\n")[0]
        print(f"[{item['type'].upper()}] {item['name']}: {first_line}")

    # 3. Retrieve and execute the functional skill
    print("\n--- Executing Discovered Skill ---")
    my_skill = tool_registry.get_skill("market_sentiment_analyzer")
    if my_skill:
        result = await my_skill.execute(ticker="AAPL")
        print(f"Result for AAPL: {result}")


if __name__ == "__main__":
    asyncio.run(main())
