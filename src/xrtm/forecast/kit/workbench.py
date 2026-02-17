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

import logging
from typing import List

from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.kit.agents.llm import LLMAgent

logger = logging.getLogger(__name__)


class AnalystWorkbench:
    r"""
    A workbench for assembling analysts and tools into orchestrator graphs.
    """
    def __init__(self, agents: List[LLMAgent], name: str = "AnalystWorkbench"):
        self.agents = agents
        self.name = name

    def build_orchestrator(self, reviewer_prompt: str) -> Orchestrator:
        orch = Orchestrator()
        research_nodes = []
        for agent in self.agents:
            node_name = f"research_{agent.name.lower()}"
            orch.add_node(node_name, agent.run)
            research_nodes.append(node_name)
        orch.add_parallel_group("research_phase", research_nodes)
        orch.set_entry_point("research_phase")
        human_node = f"human:{reviewer_prompt}"
        orch.add_edge("research_phase", human_node)
        return orch


__all__ = ["AnalystWorkbench"]
