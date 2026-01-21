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
from typing import Callable, List, Optional

from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.graph import BaseGraphState

from .aggregators import create_ivw_aggregator

logger = logging.getLogger(__name__)


class RecursiveConsensus:
    r"""
    A topology that implements 'Recursive Peer Review' with optional Red Team.

    Flow:
    1. Parallel Analysis: Multiple agents generate independent forecasts.
    2. Aggregation: Results are combined (mean/weighted).
    3. Red Team (optional): A Devil's Advocate challenges the consensus.
    4. Supervisor Check: A meta-agent checks if the confidence > threshold.
    5. Loop: If low confidence, loop back to analysis with 'critique' context.

    Args:
        analyst_wrappers (`List[Callable]`):
            List of callables (agent wrappers) that take (state, reporter) and return result.
        supervisor_wrapper (`Callable`):
             A callable that inspects the state so far and returns 'APPROVE' or 'REVISE'.
        aggregator_wrapper (`Callable`, *optional*):
             A callable that combines analyst outputs into a single forecast.
             If None and `use_ivw` is True, `create_ivw_aggregator()` is used.
        red_team_wrapper (`Callable`, *optional*):
             A callable that challenges the consensus (Devil's Advocate pattern).
        max_cycles (`int`):
             Maximum number of revision loops allowed.
        use_ivw (`bool`, *optional*, defaults to `False`):
             Whether to use Inverse Variance Weighting by default if no aggregator is provided.
    """

    def __init__(
        self,
        analyst_wrappers: List[Callable],
        supervisor_wrapper: Callable,
        aggregator_wrapper: Optional[Callable] = None,
        red_team_wrapper: Optional[Callable] = None,
        max_cycles: int = 3,
        use_ivw: bool = False,
    ):
        self.analysts = analyst_wrappers
        self.supervisor = supervisor_wrapper
        self.red_team = red_team_wrapper
        self.max_cycles = max_cycles

        if aggregator_wrapper is None:
            if use_ivw:
                self.aggregator = create_ivw_aggregator()
            else:
                raise ValueError("aggregator_wrapper must be provided if use_ivw is False")
        else:
            self.aggregator = aggregator_wrapper

    def build_graph(self) -> Orchestrator:
        r"""Constructs the executable Orchestrator graph."""
        # Orchestrator uses max_cycles for total node visits.
        # We want max_cycles to be revision loops.
        # We allow ~10 nodes per revision loop to be very safe.
        orch_max_visits = (self.max_cycles + 1) * 10
        orch = Orchestrator.create_standard(max_cycles=orch_max_visits)

        # 1. Register Analysts
        analyst_names = []
        for i, wrapper in enumerate(self.analysts):
            name = f"analyst_{i}"
            orch.add_node(name, wrapper)
            analyst_names.append(name)

        # 2. Register Aggregator & Supervisor
        orch.add_node("aggregator", self.aggregator)
        orch.add_node("supervisor", self.supervisor)

        # 3. Register Red Team (optional)
        if self.red_team:
            orch.add_node("red_team", self.red_team)

        # 4. Define Flow
        # Entry -> Parallel Analysts
        orch.add_parallel_group("parallel_analysis", analyst_names)
        orch.set_entry_point("parallel_analysis")
        orch.add_edge("parallel_analysis", "aggregator")

        # Wire Red Team if present: Aggregator -> RedTeam -> Supervisor
        if self.red_team:
            orch.add_edge("aggregator", "red_team")
            orch.add_edge("red_team", "supervisor")
        else:
            orch.add_edge("aggregator", "supervisor")

        # 5. Conditional Loop
        # Supervisor returns "APPROVE" or "REVISE"
        def check_revision(state: BaseGraphState) -> str:
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
