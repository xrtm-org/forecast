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
from typing import List

from pydantic import Field

from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.schemas.graph import BaseGraphState


# 1. Define a Custom State
# Inherit from BaseGraphState to keep required fields like subject_id and context.
class ResearchState(BaseGraphState):
    r"""Custom state container for the researcher agent workflow."""

    query: str
    findings: List[str] = Field(default_factory=list)
    is_complete: bool = False


# 2. Define Nodes that use the Custom State
async def gather_data(state: ResearchState, progress=None) -> str:
    print(f"Gathering data for: {state.query}")
    state.findings.append("Found evidence A")
    state.findings.append("Found evidence B")

    # We can still use the unstructured context for temporary flags
    state.context["raw_data_count"] = 2

    return "synthesize"


async def synthesize(state: ResearchState, progress=None) -> None:
    print(f"Synthesizing {len(state.findings)} findings...")
    state.is_complete = True
    return None


async def main():
    print("--- Starting State Management Demo ---")

    # 3. Instantiate Orchestrator with the Custom State type
    # This provides full type safety in the nodes and runners.
    orch = Orchestrator[ResearchState]()

    orch.add_node("gather", gather_data)
    orch.add_node("synthesize", synthesize)
    orch.set_entry_point("gather")
    orch.add_edge("gather", "synthesize")

    # 4. Initialize the State
    # Pydantic will validate that 'query' is provided.
    initial_state = ResearchState(
        subject_id="res_001", query="The impact of agentic workflows on developer productivity"
    )

    # 5. Run the Graph
    final_state = await orch.run(initial_state)

    print("\n--- Final Research State ---")
    print(f"Query: {final_state.query}")
    print(f"Findings: {final_state.findings}")
    print(f"Is Complete: {final_state.is_complete}")
    print(f"Context snapshot: {final_state.context}")


if __name__ == "__main__":
    asyncio.run(main())
