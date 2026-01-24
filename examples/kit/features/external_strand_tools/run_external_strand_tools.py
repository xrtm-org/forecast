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

from pydantic import SecretStr

# Import core library components
from xrtm.forecast import LLMAgent, ModelFactory, tool_registry
from xrtm.forecast.core.config.inference import GeminiConfig


# --- SIMULATION OF EXTERNAL SDK ---
# This part simulates how a third-party library like 'strand-agents' defines tools.
class ExternalStrandTool:
    """A simulated tool following the @strands.tool protocol."""

    def __init__(self):
        self.name = "get_subject_sentiment"
        self.description = "Calculates current sentiment for a subject identifier based on simulation."
        self.spec = {
            "type": "object",
            "properties": {"subject_id": {"type": "string", "description": "Subject or entity identifier."}},
            "required": ["subject_id"],
        }

    async def fn(self, subject_id: str) -> str:
        # Business logic from the external library
        return f"Sentiment for {subject_id} is positive (+0.65)."


# --- INTEGRATION EXAMPLE ---


async def main():
    # 1. Initialize an external tool (e.g., from strand-agents)
    strand_tool = ExternalStrandTool()
    print(f"[App] Ingesting external tool: {strand_tool.name}")

    # 2. Register it with xrtm-forecast using the protocol adapter
    # In a real app, you'd just do: tool_registry.register_strand_tool(strand_tool)
    tool_registry.register_strand_tool(strand_tool)

    # 3. Setup our Agent to use this tool
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[Abort] GEMINI_API_KEY not found. Please set it to run the real LLM handshake.")
        return

    config = GeminiConfig(model_id="gemini-2.0-flash-lite", api_key=SecretStr(api_key))
    model = ModelFactory.get_provider(config)

    # We create a generic analyst that knows it can use registry tools
    class ResearchAgent(LLMAgent):
        async def run(self, input_data: str, **kwargs):
            # Fetch tools by name from the registry
            subject_id = input_data
            tools = self.get_tools(["get_subject_sentiment"])

            prompt = f"Using the available tools, analyze {subject_id} and provide a summary."

            print(f"[Agent] Running research mission for {subject_id}...")
            # The model will automatically detect the tool schema and call it
            response = await self.model.generate_content_async(prompt, tools=tools)
            return response.text

    # 4. Execute the reasoning mission
    agent = ResearchAgent(model=model, name="Researcher")
    result = await agent.run("Global_Warming_2026")

    print("\n" + "=" * 50)
    print("FINAL AGENT REPORT (Using External Strand Tool):")
    print(result)
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
