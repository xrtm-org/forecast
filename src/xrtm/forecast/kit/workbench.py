# coding=utf-8
# Copyright 2026 XRTM Team. All rights reserved.

import logging
from typing import List

from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.kit.agents.llm import LLMAgent

logger = logging.getLogger(__name__)


class AnalystWorkbench:
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
