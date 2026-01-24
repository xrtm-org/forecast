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
from typing import Optional

from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.schemas.graph import BaseGraphState

# Configure logging to see the state transitions
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CORE_DEMO")


# 1. Define Nodes (Pure Python Functions)
# Nodes receive the current state and return the name of the next node (or None).


async def counter_step(state: BaseGraphState, progress=None) -> Optional[str]:
    # Demonstrate reading/writing to context
    current_count = state.context.get("count", 0)
    current_count += 1
    state.context["count"] = current_count

    logger.info(f"Counter incremented to: {current_count}")

    if current_count < 3:
        return "counter_step"  # Loop back
    return "final_step"  # Proceed


async def final_step(state: BaseGraphState, progress=None) -> None:
    logger.info("Reached the end of the graph!")
    state.context["status"] = "finished"
    return None  # Stop execution


async def main():
    logger.info("--- Starting Orchestrator Basics Demo ---")

    # 2. Instantiate the Engine
    # The Orchestrator is a generic class, but defaults to BaseGraphState.
    orch = Orchestrator[BaseGraphState]()

    # 3. Register Nodes
    orch.add_node("counter_step", counter_step)
    orch.add_node("final_step", final_step)

    # 4. Set Entry Point
    orch.set_entry_point("counter_step")

    # 5. Execute
    initial_state = BaseGraphState(subject_id="demo_001")
    initial_state.context["count"] = 0

    final_state = await orch.run(initial_state)

    print("\n--- Execution Result ---")
    print(f"Final Count: {final_state.context['count']}")
    print(f"Status: {final_state.context['status']}")


if __name__ == "__main__":
    asyncio.run(main())
