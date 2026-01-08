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
import os

from forecast.agents.llm import LLMAgent
from forecast.inference.factory import ModelFactory
from forecast.skills.web_search import WebSearchSkill


async def main():
    # 1. Setup - Using a real model if API key is present
    from forecast.inference.config import OpenAIConfig

    config = OpenAIConfig(api_key=os.getenv("OPENAI_API_KEY", "mock-key"), model_id="gpt-4o")
    factory = ModelFactory()
    model = factory.get_provider(config)

    # 2. Instantiate a Generic Agent
    agent = LLMAgent(model=model, name="Researcher")
    agent.model = model  # Set model manually for this example

    # 3. Equip the Agent with a Skill
    # Note: Requires TAVILY_API_KEY in environment for actual search
    search_skill = WebSearchSkill()
    agent.add_skill(search_skill)

    print(f"Agent '{agent.name}' equipped with skills: {list(agent.skills.keys())}")

    # 4. Use the Skill
    # We can call it directly from the agent
    if "web_search" in agent.skills:
        print("\n--- Executing WebSearchSkill ---")
        query = "What is the latest price of Bitcoin?"
        print(f"Query: {query}")

        # In a real scenario, the Agent's internal logic would decide to call this.
        # Here we demonstrate the plumbing.
        result = await agent.get_skill("web_search").execute(query=query)
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
