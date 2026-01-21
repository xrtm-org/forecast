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
import random
from typing import Any

from forecast.core.runtime import AsyncRuntime
from forecast.core.schemas.graph import BaseGraphState
from forecast.kit.topologies.consensus import RecursiveConsensus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("consensus_demo")


async def main():
    logger.info("=== Starting Recursive Consensus Demo ===")

    # --- 1. Define Mock Analyst Agents ---
    # In a real app, these would be Agent instances calling LLMs.
    async def analyst_behavior(state: BaseGraphState, reporter: Any) -> BaseGraphState:
        # Simulate thinking
        await asyncio.sleep(0.1)
        cycle = state.cycle_count

        # Each analyst generates a slightly different forecast based on the cycle
        base_confidence = 0.6 if cycle < 3 else 0.95
        noise = random.uniform(-0.05, 0.05)
        confidence = max(0.0, min(1.0, base_confidence + noise))

        # We also provide uncertainty for IVW
        uncertainty = max(0.01, (1.0 - confidence) * random.uniform(0.5, 1.5))

        forecast = {
            "confidence": confidence,
            "uncertainty": uncertainty,
            "reasoning": f"Based on cycle {cycle}, I am {confidence:.2f} confident.",
        }

        # Use the standard key expected by the default aggregator
        results = state.context.get("analyst_outputs", [])
        results.append(forecast)
        state.context["analyst_outputs"] = results

        return None

    # --- 2. Define Supervisor ---
    async def supervisor_behavior(state: BaseGraphState, reporter: Any) -> Any:
        # Use the standard 'aggregate' structure produced by ivw_aggregator
        agg = state.context.get("aggregate", {})
        score = agg.get("confidence", 0.0)
        threshold = 0.9

        if score >= threshold:
            decision = "APPROVE"
            logger.info(f"Supervisor: Confidence {score:.2f} >= {threshold}. APPROVING.")
        else:
            decision = "REVISE"
            logger.info(f"Supervisor: Confidence {score:.2f} < {threshold}. REVISING.")

        state.context["decision"] = decision

        # Clear analyst outputs for the next possible revision cycle
        state.context["analyst_outputs"] = []

        return None

    # --- 3. Define Red Team Agent ---
    # This simulates a 'Devil's Advocate' that challenges the consensus.
    async def red_team_behavior(state: BaseGraphState, reporter: Any) -> Any:
        logger.info("🚨 Red Team: Challenging the consensus with contrarian views.")
        # In a real system, the Red Team adds critique to the context
        state.context["past_critique"] = "Research indicates possible market saturation not accounted for."
        return None

    # --- 4. Assemble Topology ---
    # We wrap the behavior function 3 times to simulate 3 different analysts
    analysts = [analyst_behavior, analyst_behavior, analyst_behavior]

    topology = RecursiveConsensus(
        analyst_wrappers=analysts,
        supervisor_wrapper=supervisor_behavior,
        red_team_wrapper=red_team_behavior,  # Optional Devil's Advocate!
        use_ivw=True,
        max_cycles=5,
    )

    orch = topology.build_graph()

    # --- 5. Execution ---
    initial_state = BaseGraphState(subject_id="demo_question_1")
    final_state = await orch.run(initial_state)

    print("\n=== Final Trace ===")
    print("Execution Path:", " -> ".join(final_state.execution_path))
    print("Final Decision:", final_state.context.get("decision"))
    print("Total Nodes Visited:", final_state.cycle_count)


if __name__ == "__main__":
    AsyncRuntime.run_main(main())
