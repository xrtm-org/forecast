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
import time
from typing import Any, Callable, Dict, Optional

from forecast.graph.config import GraphConfig
from forecast.schemas.graph import BaseGraphState

logger = logging.getLogger(__name__)


class Orchestrator:
    r"""
    A state-machine based engine for managing complex agent workflows.

    The `Orchestrator` is a domain-agnostic reasoning engine that processes a
    `BaseGraphState` through a series of registered "nodes" (functions). It allows
    for iterative reasoning, conditional branching, and global usage tracking.

    Args:
        config (`GraphConfig`, *optional*):
            The configuration for the graph engine. If `None`, defaults are used.
    """

    def __init__(self, config: Optional[GraphConfig] = None):
        self.config = config or GraphConfig()
        self.max_cycles = self.config.max_cycles
        # Registry of nodes (functions) that process the state
        # format: {"node_name": callable}
        self.nodes: Dict[str, Callable] = {}

    @classmethod
    def create_standard(cls, max_cycles: Optional[int] = None) -> "Orchestrator":
        r"""
        Creates an orchestrator instance with standard platform defaults.

        Args:
            max_cycles (`int`, *optional*):
                Override for the maximum reasoning iterations allowed.

        Returns:
            `Orchestrator`: A pre-configured orchestrator instance.
        """
        config = GraphConfig()
        if max_cycles is not None:
            config.max_cycles = max_cycles
        return cls(config=config)

    def register_node(self, name: str, func: Callable) -> None:
        r"""
        Registers a processing node in the graph registry.

        Args:
            name (`str`):
                The unique identifier for the node.
            func (`Callable`):
                The function to execute for this node. Expected signature:
                `async def node_func(state: BaseGraphState, report_progress: Callable) -> Optional[str]`
        """
        self.nodes[name] = func

    async def run(
        self,
        state: BaseGraphState,
        entry_node: str = "ingestion",
        on_progress: Optional[Callable] = None,
        stopwatch: Optional[Any] = None,
    ) -> BaseGraphState:
        r"""
        Orchestrates the execution of the graph nodes starting from an entry point.

        This method manages the control flow of the graph, tracking the execution path,
        cycle count, and total latency. It terminates when a node returns `None`
        or `max_cycles` is reached.

        Args:
            state (`BaseGraphState`):
                The initial state object to be processed and evolved.
            entry_node (`str`, *optional*, defaults to `"ingestion"`):
                The name of the first node to execute.
            on_progress (`Optional[Callable]`, *optional*):
                A callback function for reporting progress during execution.
            stopwatch (`Optional[Any]`, *optional*):
                An optional instrumentation utility for tracking timing across nodes.

        Returns:
            `BaseGraphState`: The final evolved state after execution completes.
        """
        self.stopwatch = stopwatch

        async def report_progress(
            phase_id: float, phase: str, status: str, details: str, active_specialists: Optional[list[str]] = None
        ):
            if on_progress:
                await on_progress(phase_id, phase, status, details, active_specialists)

        start_total = time.time()
        await report_progress(0, "Graph", "START", f"Reasoning cycle for {state.subject_id}")

        active_node = entry_node
        while active_node:
            if state.cycle_count >= self.max_cycles:
                logger.warning(f"[GRAPH] Max cycles ({self.max_cycles}) reached for {state.subject_id}. Terminating.")
                break

            node_func = self.nodes.get(active_node)
            if not node_func:
                logger.error(f"[GRAPH] Unknown node: {active_node}")
                break

            # Nodes should return the name of the NEXT node, or None to terminate
            next_node = await node_func(state, report_progress)

            # Structural Trace: Track the executed node
            state.execution_path.append(active_node)

            active_node = next_node
            state.cycle_count += 1

        state.latencies["total_graph"] = time.time() - start_total
        logger.info(f"[GRAPH] Total cycle took {state.latencies['total_graph']:.2f}s")

        return state

    def aggregate_usage(self, state: BaseGraphState, agent_output: Any) -> None:
        r"""
        Aggregates token usage from an agent output into the global graph state.

        Args:
            state (`BaseGraphState`):
                The state object where usage statistics are accumulated.
            agent_output (`Any`):
                The output from an agent execution, which may contain 'usage' metadata.
        """
        usage = {}
        if hasattr(agent_output, "usage"):
            usage = agent_output.usage
        elif isinstance(agent_output, dict):
            usage = agent_output.get("usage", {})

        try:
            if isinstance(usage, dict):
                p = int(usage.get("prompt_tokens", 0) or 0)
                c = int(usage.get("completion_tokens", 0) or 0)
                t = int(usage.get("total_tokens", 0) or 0)
                state.usage["prompt_tokens"] += p
                state.usage["completion_tokens"] += c
                state.usage["total_tokens"] += t
        except Exception as e:
            logger.warning(f"[GRAPH] Usage aggregation error: {e}")


__all__ = ["Orchestrator"]
