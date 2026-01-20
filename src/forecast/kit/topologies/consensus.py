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
from typing import Callable, List

from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.graph import BaseGraphState

logger = logging.getLogger(__name__)


class RecursiveConsensus:
    r"""
    A topology that implements 'Recursive Peer Review'.

    Flow:
    1. Parallel Analysis: Multiple agents generate independent forecasts.
    2. Aggregation: Results are combined (mean/weighted).
    3. Supervisor Check: A meta-agent checks if the confidence > threshold.
    4. Loop: If low confidence, loop back to analysis with 'critique' context.

    Args:
        analyst_wrappers (`List[Callable]`):
            List of callables (agent wrappers) that take (state, reporter) and return result.
        supervisor_wrapper (`Callable`):
             A callable that inspects the state so far and returns 'APPROVE' or 'REVISE'.
        aggregator_wrapper (`Callable`):
             A callable that combines analyst outputs into a single forecast.
    """

    def __init__(
        self,
        analyst_wrappers: List[Callable],
        supervisor_wrapper: Callable,
        aggregator_wrapper: Callable,
        max_cycles: int = 3,
    ):
        self.analysts = analyst_wrappers
        self.supervisor = supervisor_wrapper
        self.aggregator = aggregator_wrapper
        self.max_cycles = max_cycles

    def build_graph(self) -> Orchestrator:
        r"""Constructs the executable Orchestrator graph."""
        orch = Orchestrator.create_standard(max_cycles=self.max_cycles)

        # 1. Register Analysts
        analyst_names = []
        for i, wrapper in enumerate(self.analysts):
            name = f"analyst_{i}"
            orch.add_node(name, wrapper)
            analyst_names.append(name)

        # 2. Register Aggregator & Supervisor
        orch.add_node("aggregator", self.aggregator)
        orch.add_node("supervisor", self.supervisor)

        # 3. Define Flow
        # Entry -> Parallel Analysts
        orch.add_parallel_group("parallel_analysis", analyst_names)
        orch.set_entry_point("parallel_analysis")
        orch.add_edge("parallel_analysis", "aggregator")
        orch.add_edge("aggregator", "supervisor")

        # 4. Conditional Loop
        # Supervisor returns "APPROVE" or "REVISE"
        def check_revision(state: BaseGraphState) -> str:
            # We assume the supervisor writes 'decision' to context or returns it
            # For this topology, let's assume the supervisor's LAST return value is checking logic
            # But Orchestrator logic is pre-computation.
            # So the supervisor node function usually updates `state.context['decision']`
            return state.context.get("decision", "REVISE")

        orch.add_conditional_edge(
            "supervisor",
            check_revision,
            {
                "APPROVE": None,  # End of graph
                "REVISE": "parallel_analysis",  # Loop back
            },
        )

        return orch


__all__ = ["RecursiveConsensus"]
