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

import logging

from forecast import AsyncRuntime, BaseGraphState
from forecast.core.tools.base import Tool
from forecast.kit.agents.fact_checker import FactCheckerAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fact_checker_demo")


class MockTool(Tool):
    @property
    def name(self):
        return "mock_search"

    @property
    def description(self):
        return "Mocks a search engine"

    @property
    def parameters_schema(self):
        return {}

    async def run(self, query: str, **kwargs) -> str:
        return f"Verified proof for: {query}"


async def main():
    logger.info("=== Starting Fact Checker Demo ===")

    # Initialize the Fact Checker Agent with a list of tools
    agent = FactCheckerAgent(tools=[MockTool()], model_id="mock-model")

    # Initial state with a context containing data to verify
    state = BaseGraphState(subject_id="demo_1")
    state.context["claims"] = ["The GDP of France grew by 4% in 2024."]

    # Run the agent (normally called by the Orchestrator)
    # Here we simulate the orchestrator calling it
    async def mock_reporter(*args):
        pass

    await agent.run(state, mock_reporter)

    print("\n=== Verification Results ===")
    results = state.context.get("fact_check_results", [])
    print(f"Verified Facts: {len(results)}")
    for res in results:
        status = "✅" if res["verified"] else "❌"
        print(f" {status} {res['claim']}: {res['evidence']}")

    if state.context.get("verification_score", 0) > 0:
        print("\n✅ Fact Checker successfully extracted and verified the claim.")


if __name__ == "__main__":
    AsyncRuntime.run_main(main())
