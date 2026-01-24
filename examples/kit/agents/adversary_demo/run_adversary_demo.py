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
from typing import Any

from xrtm.forecast import AsyncRuntime
from xrtm.forecast.kit.agents.red_team import RedTeamAgent
from xrtm.forecast.providers.inference.base import InferenceProvider, ModelResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adversary_demo")


class MockProvider(InferenceProvider):
    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs) -> Any:
        # RedTeamAgent expects a structured response
        response_text = (
            "COUNTER_ARGUMENT: The thesis assumes stable interest rates, but it fails to account for potential hikes.\n"
            "WEAKNESSES:\n"
            "- Did not consider inflation sticking\n"
            "- Ignored geopolitical risks\n"
            "- Overly reliant on past performance\n"
            "ALTERNATIVE_PROBABILITY: 0.4\n"
            "CHALLENGE_CONFIDENCE: 0.8"
        )
        return ModelResponse(text=response_text)

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs) -> Any:
        # Sync version not used in this async demo
        pass

    async def stream(self, messages: list[dict[str, str]], **kwargs):
        pass


async def main():
    logger.info("=== Starting Adversary (Red Team) Demo ===")

    # In a real scenario, this would be a real inference provider
    mock_provider = MockProvider()

    # Initialize the Red Team Agent
    agent = RedTeamAgent(model=mock_provider, intensity="moderate")

    # The thesis to challenge
    thesis = "We estimate a 90% confidence that the market will continue its bull run due to strong consumer spending and stable interest rates."

    # Run the agent
    # RedTeamAgent uses .challenge() instead of .run()
    result = await agent.challenge(thesis, reasoning="Consumer confidence metrics are at all time highs.")

    print("\n=== Original Thesis ===")
    print(thesis)

    print("\n=== Adversarial Challenge ===")
    print(f"Argument: {result.counter_argument}")
    print(f"Weaknesses: {result.weakness_points}")
    print(f"Confidence in Challenge: {result.confidence_in_challenge}")

    print("\n✅ Adversary successfully identified potential flaws in the thesis.")


if __name__ == "__main__":
    AsyncRuntime.run_main(main())
