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
import logging

from xrtm.forecast import create_local_analyst

# Setup logging to see the "Pure Core" initialization
logging.basicConfig(level=logging.INFO)


async def run_local_inference():
    r"""
    Demonstrates the 'Practical Shell' capability to spin up a private
    reasoning engine using local Hugging Face weights.
    """
    print("--- Local Analyst Example ---")

    # Using a tiny model for fast demonstration
    # In production, you might use 'meta-llama/Llama-3-8b-Instruct'
    model_path = "sshleifer/tiny-gpt2"

    print(f"Instantiating private analyst with {model_path}...")
    analyst = create_local_analyst(model_path=model_path, name="PrivateResearcher")

    print("Executing local reasoning...")
    # The 'run' method is the standardized ergonomic alias
    result = await analyst.run("What is the capital of France?")

    print("\nResult from Local Model:")
    print(f"Model: {result.metadata.get('model_id')}")
    print(f"Output: {result.reasoning}")
    print(f"Confidence: {result.confidence}")


if __name__ == "__main__":
    asyncio.run(run_local_inference())
