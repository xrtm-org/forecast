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

        # Declarative Edges: {"from_node_name": "to_node_name"}
        # This allows us to wire the graph externally.
        self.edges: Dict[str, str] = {}
        # Parallel Execution Groups: {"group_name": ["node1", "node2"]}
        self.parallel_groups: Dict[str, list[str]] = {}
        self.entry_point: Optional[str] = None

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

    def add_node(self, name: str, func: Callable) -> None:
        r"""
        Registers a processing node in the graph registry.

        Args:
            name (`str`): The unique identifier for the node.
            func (`Callable`): The function to execute.
        """
        self.nodes[name] = func

    def register_node(self, name: str, func: Callable) -> None:
        r"""Alias for add_node for backward compatibility."""
        self.add_node(name, func)

    def add_edge(self, from_node: str, to_node: str) -> None:
        r"""
        Adds a directed edge between two nodes.

        Args:
            from_node (`str`): The starting node.
            to_node (`str`): The destination node.
        """
        self.edges[from_node] = to_node

    def set_entry_point(self, node_name: str) -> None:
        r"""Sets the starting node for the graph execution."""
        self.entry_point = node_name

    def add_parallel_group(self, group_name: str, node_names: list[str]) -> None:
        r"""
        Registers a group of nodes to be executed in parallel.

        A "Parallel Group" is a named execution step that triggers multiple nodes
        concurrently. The Orchestrator waits for ALL nodes in the group to complete
        before proceeding to the next step.

        Args:
            group_name (`str`): The identifier for this parallel step.
            node_names (`list[str]`): List of existing node names to execute.

        Example:
            ```python
            orch.add_node("worker_1", w1)
            orch.add_node("worker_2", w2)
            # Define a group that runs both workers
            orch.add_parallel_group("run_workers", ["worker_1", "worker_2"])
            # Wire the graph to enter this group
            orch.add_edge("start", "run_workers")
            ```
        """
        self.parallel_groups[group_name] = node_names

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

        if entry_node == "ingestion" and self.entry_point:
            entry_node = self.entry_point

        active_node = entry_node
        while active_node:
            if state.cycle_count >= self.max_cycles:
                logger.warning(f"[GRAPH] Max cycles ({self.max_cycles}) reached for {state.subject_id}. Terminating.")
                break

            # Check if active_node is a parallel group
            if active_node in self.nodes:
                # Standard single node
                node_func = self.nodes.get(active_node)
                if not node_func:
                    logger.error(f"[GRAPH] Unknown node: {active_node}")
                    break
                next_node = await node_func(state, report_progress)
                state.execution_path.append(active_node)

            elif active_node in self.parallel_groups:
                # Parallel Group Execution
                group_nodes = self.parallel_groups[active_node]
                logger.info(f"[GRAPH] Executing parallel group: {active_node} -> {group_nodes}")

                tasks = []
                for node_name in group_nodes:
                    func = self.nodes.get(node_name)
                    if func:
                        tasks.append(func(state, report_progress))
                    else:
                        logger.error(f"[GRAPH] Unknown node in group: {node_name}")

                # Execute all workers in parallel
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for i, res in enumerate(results):
                        if isinstance(res, Exception):
                            node_name = group_nodes[i] if i < len(group_nodes) else "unknown"
                            logger.error(f"[GRAPH] Error in parallel node {node_name}: {res}")

                # Logic for parallel group next step:
                # Parallel groups don't return a single "next_node".
                # We rely on the declared edge coming OUT of the group name.
                next_node = None
                state.execution_path.append(f"parallel:{active_node}")

            else:
                logger.error(f"[GRAPH] Unknown flow control: {active_node}")
                break

            # If the node didn't explicitly return a next step (or returned None),
            # check the declarative edge registry.
            if next_node is None:
                next_node = self.edges.get(active_node)

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
