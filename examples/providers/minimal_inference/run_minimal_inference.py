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

from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.providers.inference.factory import ModelFactory


async def main():
    """
    Shows how to use the Inference Layer directly.
    This is the lowest level of the library.
    """
    # 1. Setup Configuration
    # We default to GPT-4o-mini for efficiency
    config = OpenAIConfig(api_key=os.getenv("OPENAI_API_KEY", "mock-key"), model_id="gpt-4o-mini")

    # 2. Get Provider via Factory
    factory = ModelFactory()
    provider = factory.get_provider(config)

    print(f"Provider: {provider.__class__.__name__}")

    # 3. Simple Generation
    prompt = "Explain Bayesian reasoning in one sentence."
    print(f"\nPrompt: {prompt}")

    try:
        # Note: If API key is 'mock-key', this will naturally fail or return a mock if implemented
        response = await provider.generate_content_async(prompt)
        print(f"\nResponse: {response.text}")
        print(f"\nUsage: {response.usage}")
    except Exception as e:
        print(f"\nGeneration failed (Expected if no API key): {e}")


if __name__ == "__main__":
    asyncio.run(main())
