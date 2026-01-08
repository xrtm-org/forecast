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

from typing import Any, Optional

from forecast.agents.base import Agent
from forecast.graph.orchestrator import Orchestrator
from forecast.schemas.graph import BaseGraphState


class GraphAgent(Agent):
    """
    Agent that encapsulates a sub-graph (Orchestrator).
    Enables 'Composite Nodes' where an agent internally runs a whole pipeline.
    """

    def __init__(self, orchestrator: Orchestrator, entry_node: Optional[str] = None, name: Optional[str] = None):
        super().__init__(name)
        self.orchestrator = orchestrator
        self.entry_node = entry_node

    async def run(self, input_data: Any, **kwargs) -> Any:
        """
        Runs the internal orchestrator.
        Converts input_data into a BaseGraphState context.
        """
        # Create a fresh state for the sub-graph
        state = BaseGraphState(subject_id=f"subgraph_{self.name}")
        state.context = {"input": input_data, **kwargs}

        start_node = self.entry_node or self.orchestrator.entry_point or "ingestion"
        await self.orchestrator.run(state, entry_node=start_node)

        # Return the final context or a specific output if defined in state
        return state.context.get("output", state.context)
