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
from xrtm.forecast.kit.agents.specialists.adversary import AdversaryAgent
from xrtm.forecast.providers.inference.base import InferenceProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adversary_demo")


class MockProvider(InferenceProvider):
    async def generate(self, prompt: str, **kwargs) -> Any:
        return (
            "COUNTER-ARGUMENT: The thesis assumes stable interest rates, but it fails to account for potential hikes."
        )

    async def run(self, *args, **kwargs):
        pass

    async def stream(self, *args, **kwargs):
        pass


async def main():
    logger.info("=== Starting Adversary (Red Team) Demo ===")

    # In a real scenario, this would be a real inference provider
    mock_provider = MockProvider()

    # Initialize the Adversary Agent
    agent = AdversaryAgent(model=mock_provider)

    # The thesis to challenge
    thesis = "We estimate a 90% confidence that the market will continue its bull run due to strong consumer spending and stable interest rates."

    # Run the agent
    challenge = await agent.run(thesis)

    print("\n=== Original Thesis ===")
    print(thesis)

    print("\n=== Adversarial Challenge ===")
    print(challenge)

    print("\n✅ Adversary successfully identified potential flaws in the thesis.")


if __name__ == "__main__":
    AsyncRuntime.run_main(main())
