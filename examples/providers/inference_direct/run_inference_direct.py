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

from forecast.core.config.inference import OpenAIConfig
from forecast.providers.inference.factory import ModelFactory


async def main():
    print("--- Starting Direct Inference Demo ---")

    # 1. Initialize the Model Factory
    # The factory handles provider lifecycle and configuration.
    factory = ModelFactory()

    # 2. Configure a Provider (Directly)
    # Note: This requires an OPENAI_API_KEY environment variable if run live.
    # For this demo, we show the configuration pattern.
    config = OpenAIConfig(api_key=os.getenv("OPENAI_API_KEY", "mock-key"), model_name="gpt-4o")

    # 3. Get the Provider
    # In Pure Core, you can interact with providers without creating an Agent.
    try:
        provider = factory.get_provider("openai", config)

        print(f"Using provider: {provider.__class__.__name__}")

        # prompt = "Explain the 'Pure Core' architectural pattern in 2 sentences."

        # 4. Non-Streaming Call
        print("\n[Requesting completion...]")
        # result = await provider.generate_content_async(prompt)
        # print(f"Response: {result.text}")
        print("(Actual LLM call commented out for environment safety in examples)")

        # 5. Streaming Call (Standardized Protocol)
        print("\n[Demonstrating streaming loop structure...]")
        # async for chunk in provider.stream(prompt):
        #     if "contentBlockDelta" in chunk:
        #         text = chunk["contentBlockDelta"]["delta"]["text"]
        #         print(text, end="", flush=True)

        print("\nStream loop would execute here using the generic protocol.")

    except Exception as e:
        print(f"Error initializing provider: {e}")
        print("Note: Ensure API keys are set for live provider testing.")


if __name__ == "__main__":
    asyncio.run(main())
