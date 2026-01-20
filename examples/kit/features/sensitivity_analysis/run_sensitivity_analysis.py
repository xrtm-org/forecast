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

from forecast.core.config.graph import GraphConfig
from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.graph import BaseGraphState
from forecast.kit.scenarios import ScenarioManager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# 1. Define State
class SubjectState(BaseGraphState):
    """Represents the state of a forecasting subject prediction."""

    base_value: float = 100.0
    sentiment_score: float = 0.5  # 0 to 1
    volatility_factor: float = 1.0
    final_forecast: float = 0.0
    rationale: str = ""


# 2. Define Stages (Nodes)
async def analyze_sentiment(state: SubjectState, on_progress=None) -> None:
    """Simulates an LLM analyzing news sentiment."""
    # In a real app, this would use an LLM provider
    logger.info(f"[{state.subject_id}] Analyzing sentiment...")
    state.rationale += f"Sentiment analyzed at {state.sentiment_score}. "
    return None


async def calculate_forecast(state: SubjectState, on_progress=None) -> None:
    """Applies the model logic."""
    logger.info(f"[{state.subject_id}] Calculating forecast with vol={state.volatility_factor}...")

    impact = (state.sentiment_score - 0.5) * 50 * state.volatility_factor
    state.final_forecast = state.base_value + impact

    state.rationale += f"Forecast {state.final_forecast} (Impact: {impact})."
    return None


async def main():
    print("--- 🔮 Scenario Branching (Sensitivity Analysis) Demo ---")

    # 3. Setup Orchestrator
    config = GraphConfig(max_cycles=5)
    orchestrator = Orchestrator(config)

    orchestrator.add_node("analyze", analyze_sentiment)
    orchestrator.add_node("forecast", calculate_forecast)

    orchestrator.add_edge("analyze", "forecast")
    orchestrator.set_entry_point("analyze")

    # 4. Initialize Manager
    manager = ScenarioManager(orchestrator)

    # 5. Define Scenarios
    # Scenario A: Control (Standard conditions)
    manager.add_branch("Control", overrides={"subject_id": "control-run", "volatility_factor": 1.0})

    # Scenario B: High Volatility Shock
    manager.add_branch(
        "High_Vol_Shock",
        overrides={
            "subject_id": "shock-run",
            "volatility_factor": 5.0,
            "sentiment_score": 0.8,  # Also assume highly positive news
        },
    )

    # Scenario C: Downward Trajectory
    manager.add_branch(
        "Downward_Trajectory", overrides={"subject_id": "crash-run", "volatility_factor": 2.0, "sentiment_score": 0.2}
    )

    # 6. Run Execution
    initial_state = SubjectState(subject_id="template", base_value=100.0, sentiment_score=0.5)

    print("\nRunning scenarios in parallel...")
    results = await manager.run_all(initial_state)

    # 7. Print Report
    print("\n--- 📊 Sensitivity Report ---")
    print(f"{'Scenario':<20} | {'Value':<10} | {'Rationale'}")
    print("-" * 80)

    for name, state in results.items():
        print(f"{name:<20} | {state.final_forecast:<10.2f} | {state.rationale}")


if __name__ == "__main__":
    asyncio.run(main())
