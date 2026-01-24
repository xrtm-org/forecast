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

r"""
Sentinel Protocol Demo: Dynamic Forecasting.

This example demonstrates the Sentinel PollingDriver for tracking how
forecasts evolve over time ("living forecasts").

Usage:
    uv run python examples/kit/run_sentinel_demo.py
"""

import asyncio
from datetime import timedelta

from xrtm.forecast.core.schemas.forecast import ForecastQuestion
from xrtm.forecast.kit.sentinel import PollingDriver, TriggerRules


class MockInferenceProvider:
    r"""A mock inference provider for demonstration."""

    def __init__(self) -> None:
        self._call_count = 0

    async def generate(self, prompt: str) -> "MockResponse":
        self._call_count += 1
        # Simulate probability drift over time
        import random

        new_prob = 0.5 + (self._call_count * 0.05) + random.uniform(-0.1, 0.1)
        new_prob = max(0.0, min(1.0, new_prob))

        return MockResponse(
            f"NEW_PROBABILITY: {new_prob:.2f}\nREASONING: Update #{self._call_count} - simulated market conditions."
        )


class MockResponse:
    def __init__(self, text: str) -> None:
        self.text = text


async def main() -> None:
    r"""Run the Sentinel demo."""
    print("=" * 60)
    print("SENTINEL PROTOCOL DEMO: Dynamic Forecasting")
    print("=" * 60)
    print()

    # Create a mock model
    model = MockInferenceProvider()

    # Create the polling driver with a short interval for demo
    driver = PollingDriver(
        model=model,  # type: ignore
        default_interval=2.0,  # 2 seconds for demo (normally 1 hour)
    )

    # Create a question to track
    question = ForecastQuestion(
        id="fed_rate_hike_2026",
        title="Will the Federal Reserve raise interest rates in Q1 2026?",
        content="Tracking Fed policy decisions based on inflation data.",
    )

    # Set up trigger rules
    rules = TriggerRules(
        interval=timedelta(seconds=1),  # Check every second (demo mode)
        max_updates=5,  # Stop after 5 updates
    )

    # Register the watch with initial confidence
    print(f"📊 Registering watch for: {question.title}")
    print("   Initial confidence: 50%")
    print(f"   Max updates: {rules.max_updates}")
    print()

    watch_id = await driver.register_watch(
        question=question,
        rules=rules,
        initial_confidence=0.5,
    )

    print(f"✅ Watch registered: {watch_id}")
    print()
    print("Starting polling loop...")
    print("-" * 60)

    # Run the polling loop (will stop after max_updates)
    await driver.run(max_cycles=5)

    print("-" * 60)
    print()

    # Get the final trajectory
    trajectory = await driver.get_trajectory(watch_id)
    if trajectory:
        print("📈 FORECAST TRAJECTORY:")
        print(f"   Question: {trajectory.question_id}")
        print(f"   Final Confidence: {trajectory.final_confidence:.1%}")
        print(f"   Total Points: {len(trajectory.points)}")
        print()
        print("   Timeline:")
        for i, point in enumerate(trajectory.points):
            print(f"   [{i}] {point.timestamp.strftime('%H:%M:%S')} → {point.value:.1%}")
        print()
        print("   Rationale History:")
        for i, rationale in enumerate(trajectory.rationale_history):
            print(f"   [{i}] {rationale[:60]}...")

    print()
    print("=" * 60)
    print("Demo complete. In production, use longer intervals (e.g., 1 hour)")
    print("and connect to real search/news APIs for information retrieval.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
