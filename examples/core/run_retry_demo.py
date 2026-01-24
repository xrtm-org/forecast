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

r"""
Resilience Protocol Demo
=======================

This script demonstrates the production-grade retry capabilities of the ResilientProvider.
It simulates a flaky inference provider that fails intermittently and shows how
the resilience layer handles these failures with jittered exponential backoff.

Usage:
    python run_retry_demo.py
"""

import asyncio
import logging
import random
import time

from xrtm.forecast.core.resilience import ResilientProvider
from xrtm.forecast.core.resilience.wrapper import RetryConfig

# Configure logging to show retry attempts
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("RetryDemo")


class FlakyProvider:
    r"""A mock provider that fails randomly."""

    def __init__(self, failure_rate: float = 0.7):
        self.failure_rate = failure_rate
        self.call_count = 0
        self.model_id = "flaky-gpt-4"

    async def generate(self, prompt: str) -> str:
        r"""Simulate generation with random failures."""
        self.call_count += 1
        logger.info(f"  -> Attempt {self.call_count} calling provider...")

        # Simulate network latency
        await asyncio.sleep(0.1)

        if random.random() < self.failure_rate:
            error_type = random.choice([ConnectionError, TimeoutError, OSError])
            raise error_type(f"Simulated {error_type.__name__} failure")

        return f"Success! Response to: {prompt}"


def on_retry_callback(attempt: int, exc: Exception, wait_time: float):
    r"""Callback to monitor retry behavior."""
    logger.warning(f"  [Middleware] Caught {type(exc).__name__}. Retrying in {wait_time:.2f}s (Attempt {attempt + 1})")


async def main():
    print("=" * 60)
    print("Resilience Protocol Demo")
    print("=" * 60)
    print("\n1. Initializing FlakyProvider (70% failure rate)")
    flaky = FlakyProvider(failure_rate=0.7)

    print("\n2. Wrapping with ResilientProvider")
    # Configure aggressive backoff for demo speed
    config = RetryConfig(
        max_retries=5,
        initial_wait=0.5,  # Start with 0.5s
        exponential_base=2.0,
        jitter=True,
    )

    resilient = ResilientProvider(flaky, config=config, on_retry=on_retry_callback)

    print("\n3. Executing resilient call...")
    start_time = time.time()

    try:
        response = await resilient.execute_with_retry(flaky.generate, "Hello World")
        duration = time.time() - start_time

        print(f"\nSUCCESS! Result: {response}")
        print(f"Total duration: {duration:.2f}s")

    except Exception as e:
        print(f"\nFAILED after all retries: {e}")

    print("\n4. Statistics:")
    stats = resilient.stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
