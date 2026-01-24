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

from xrtm.forecast import ModelFactory, RoutingAgent


async def run_tiered_reasoning():
    r"""
    Demonstrates 'Tiered Reasoning' by routing between a local tiny model
    and a cloud-based smart model.
    """
    print("--- Tiered Reasoning Example ---")

    # 1. Setup our tiers
    # 'Fast' tier uses a local model (Sovereign/Cheap)
    fast_model = ModelFactory.get_provider("hf:sshleifer/tiny-gpt2")

    # 'Smart' tier uses a frontier model (Sophisticated/Costly)
    smart_model = ModelFactory.get_provider("gemini:gemini-2.0-flash")

    # 2. Instantiate the Router
    # It uses a default router model (Gemini-Flash) to classify the task
    router = RoutingAgent(fast_tier=fast_model, smart_tier=smart_model, name="EfficiencyRouter")

    # 3. Simple Task (Expect FAST route)
    print("\nExecuting Simple Task...")
    res_fast = await router.run("Format this name: john doe -> John Doe")

    # 4. Complex Task (Expect SMART route)
    print("\nExecuting Complex Task...")
    res_smart = await router.run(
        "Analyze the causal relationship between rising interest rates and regional housing supply elasticity in 2026."
    )

    print("\n--- Summary ---")
    print(f"Simple Task Result (from local/fast): {res_fast}")
    print(f"Complex Task Result (from cloud/smart): {res_smart.text[:100]}...")


if __name__ == "__main__":
    asyncio.run(run_tiered_reasoning())
