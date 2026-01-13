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
        # Cycle 0 (First Pass): Low confidence
        # Cycle 1+ (Refinement): High confidence
        base_confidence = 0.6 if cycle < 3 else 0.95
        noise = random.uniform(-0.05, 0.05)
        confidence = max(0.0, min(1.0, base_confidence + noise))

        # This is a hack for the demo because reporter isn't the agent
        # Actually reporter is the report_progress function.
        # We rely on the orchestrator's task naming if we want exact ID,
        # but here we just push to a shared bucket.

        forecast = {"confidence": confidence, "reasoning": f"Based on cycle {cycle}, I am {confidence:.2f} confident."}

        # Thread-safe append? The Orchestrator runs parallel groups.
        # Dicts are thread-safe for atomic ops in GIL, but let's be safe:
        # We'll just assume atomic append to a list in context.
        # In production, use state locking or merge steps.
        results = state.context.get("results", [])
        results.append(forecast)
        state.context["results"] = results

        return None

    # --- 2. Define Aggregator ---
    async def aggregator_behavior(state: BaseGraphState, reporter: Any) -> Any:
        results = state.context.get("results", [])
        if not results:
            state.context["aggregate"] = 0.0
            return None

        # Average confidence
        avg_conf = sum(r["confidence"] for r in results) / len(results)
        state.context["aggregate"] = avg_conf

        # Clear results for next pass so we don't double count
        # In a real system, we might want to keep history.
        state.context["history"] = state.context.get("history", []) + results
        state.context["results"] = []

        logger.info(f"cycle {state.cycle_count} | Aggregated Confidence: {avg_conf:.2f}")
        return None

    # --- 3. Define Supervisor ---
    async def supervisor_behavior(state: BaseGraphState, reporter: Any) -> Any:
        score = state.context.get("aggregate", 0.0)
        threshold = 0.9

        if score >= threshold:
            decision = "APPROVE"
            logger.info(f"Supervisor: Confidence {score:.2f} >= {threshold}. APPROVING.")
        else:
            decision = "REVISE"
            logger.info(f"Supervisor: Confidence {score:.2f} < {threshold}. REVISING.")

        state.context["decision"] = decision
        return None

    # --- 4. Assemble Topology ---
    # We wrap the behavior function 3 times to simulate 3 different analysts
    # Note: In a real system, these would be distinct Agent instances.
    analysts = [analyst_behavior, analyst_behavior, analyst_behavior]

    topology = RecursiveConsensus(
        analyst_wrappers=analysts,
        supervisor_wrapper=supervisor_behavior,
        aggregator_wrapper=aggregator_behavior,
        max_cycles=10,
    )

    orch = topology.build_graph()

    # --- 5. Execution ---
    initial_state = BaseGraphState(subject_id="demo_question_1")
    final_state = await orch.run(initial_state)

    print("\n=== Final Trace ===")
    print("Execution Path:", " -> ".join(final_state.execution_path))
    print("Final Decision:", final_state.context.get("decision"))
    print("Total Cycles:", final_state.cycle_count)


if __name__ == "__main__":
    asyncio.run(main())
