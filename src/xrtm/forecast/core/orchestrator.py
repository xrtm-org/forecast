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
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from xrtm.forecast.core.config.graph import GraphConfig
from xrtm.forecast.core.interfaces import HumanProvider
from xrtm.forecast.core.runtime import AsyncRuntime
from xrtm.forecast.core.schemas.graph import BaseGraphState

logger = logging.getLogger(__name__)

StateT = TypeVar("StateT", bound=BaseGraphState)


class Orchestrator(Generic[StateT]):
    r"""
    A state-machine based engine for managing complex agent workflows.

    The `Orchestrator` is a domain-agnostic reasoning engine that processes a
    `BaseGraphState` through a series of registered "stages" (functions). It allows
    for iterative reasoning, conditional branching, and global usage tracking.

    Args:
        config (`GraphConfig`, *optional*):
            The configuration for the graph engine. If `None`, defaults are used.
    r"""

    def __init__(self, config: Optional[GraphConfig] = None):
        self.config = config or GraphConfig()
        self.max_cycles = self.config.max_cycles
        # Registry of stages (functions) that process the state
        # format: {"stage_name": callable}
        self.nodes: Dict[str, Callable] = {}

        # Declarative Edges: {"from_node_name": "to_node_name"}
        # This allows us to wire the graph externally.
        self.edges: Dict[str, str] = {}
        # Conditional Edges: {"from_node": (condition_func, route_map)}
        self.conditional_edges: Dict[str, tuple] = {}
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

        Example:
            ```python
            from xrtm.forecast import Orchestrator
            orch = Orchestrator.create_standard(max_cycles=5)
            ```
        r"""
        config = GraphConfig()
        if max_cycles is not None:
            config.max_cycles = max_cycles
        return cls(config=config)

    def add_node(self, name: str, func: Callable) -> None:
        r"""
        Registers a processing stage in the graph registry.

        Args:
            name (`str`): The unique identifier for the stage.
            func (`Callable`): The function to execute.

        Returns:
            `None`

        Example:
            ```python
            orch.add_node("research", my_research_func)
            ```
        r"""
        self.nodes[name] = func

    def register_node(self, name: str, func: Callable) -> None:
        r"""Alias for add_node for backward compatibility."""
        self.add_node(name, func)

    def add_edge(self, from_node: str, to_node: str) -> None:
        r"""
        Adds a directed edge between two stages.

        Args:
            from_node (`str`): The starting stage.
            to_node (`str`): The destination stage.
        r"""
        self.edges[from_node] = to_node

    def set_entry_point(self, node_name: str) -> None:
        r"""Sets the starting stage for the graph execution."""
        self.entry_point = node_name

    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable[[BaseGraphState], str],
        route_map: Dict[str, str],
    ) -> None:
        r"""
        Adds a logic-based routing step.

        Args:
            from_node (`str`): The source node.
            condition (`Callable[[BaseGraphState], str]`):
                A function that inspects the state and returns a routing key.
            route_map (`Dict[str, str]`):
                A mapping from the routing key to the next node name.
        r"""
        self.conditional_edges[from_node] = (condition, route_map)

    def add_parallel_group(self, group_name: str, node_names: list[str]) -> None:
        r"""
        Registers a group of stages to be executed in parallel.

        A "Parallel Group" is a named execution step that triggers multiple stages
        concurrently. The Orchestrator waits for ALL stages in the group to complete
        before proceeding to the next step.

        Args:
            group_name (`str`): The identifier for this parallel step.
            node_names (`list[str]`): List of existing stage names to execute.

        Example:
            ```python
            orch.add_node("worker_1", w1)
            orch.add_node("worker_2", w2)
            # Define a group that runs both workers
            orch.add_parallel_group("run_workers", ["worker_1", "worker_2"])
            # Wire the graph to enter this group
            orch.add_edge("start", "run_workers")
            ```
        r"""
        self.parallel_groups[group_name] = node_names

    async def run(
        self,
        state: BaseGraphState,
        entry_node: str = "ingestion",
        on_progress: Optional[Any] = None,
        stopwatch: Optional[Any] = None,
    ) -> BaseGraphState:
        r"""
        Orchestrates the execution of the graph stages starting from an entry point.
        """
        from xrtm.forecast.core.runtime import temporal_context_var

        # Set the temporal context for this reasoning task
        token = temporal_context_var.set(state.temporal_context)
        self.stopwatch = stopwatch
        try:

            async def report_progress(
                phase_id: float,
                phase: str,
                status: str,
                details: str,
                active_specialists: Optional[list[str]] = None,
            ):
                if on_progress:
                    await on_progress(phase_id, phase, status, details, active_specialists)

            start_total = time.time()
            await report_progress(0, "Graph", "START", f"Reasoning cycle for {state.subject_id}")

            if entry_node == "ingestion" and self.entry_point:
                entry_node = self.entry_point

            active_node: Optional[str] = entry_node
            while active_node:
                next_node = None
                if state.cycle_count >= self.max_cycles:
                    logger.warning(
                        f"[GRAPH] Max cycles ({self.max_cycles}) reached for {state.subject_id}. Terminating."
                    )
                    break

                state.cycle_count += 1
                # Check if active_node is a standard node or a native primitive
                if active_node in self.nodes:
                    # Merkle Anchoring: Capture parent state before execution
                    state.parent_hash = state.state_hash

                    # Standard single node
                    node_func = self.nodes.get(active_node)
                    if node_func:
                        # Temporal Sandboxing: Mock System Clock
                        if state.temporal_context and state.temporal_context.is_backtest:
                            from freezegun import freeze_time

                            with freeze_time(state.temporal_context.reference_time):
                                res = await node_func(state, report_progress)
                        else:
                            res = await node_func(state, report_progress)

                        # Automatically capture node results
                        state.node_reports[active_node] = res

                        # If the node returned a string, check if it's a valid next node
                        if isinstance(res, str) and (
                            res in self.nodes or res in self.parallel_groups or res.startswith("human:")
                        ):
                            next_node = res
                        else:
                            next_node = None
                    elif not active_node.startswith("human:"):
                        logger.error(f"[GRAPH] Unknown node (function is None): {active_node}")
                        break

                    if active_node.startswith("human:"):
                        pass  # Fall through to common anchor logic if we move the human logic up

                # Native Primitive: Human Intervention
                if active_node.startswith("human:"):
                    prompt = active_node.split("human:", 1)[1]
                    logger.info(f"[GRAPH] Waiting for human input: {prompt}")

                    # We look for a HumanProvider in the context
                    provider: Optional[HumanProvider] = state.context.get("human_provider")
                    if not provider:
                        logger.error(
                            "[GRAPH] Human intervention requested but no 'human_provider' found in state context."
                        )
                        break

                    human_val = await provider.get_human_input(prompt)
                    state.node_reports[active_node] = human_val
                    next_node = None

                    # Common Anchor Logic (Merkle)
                    state.execution_path.append(active_node)
                    state.state_hash = state.compute_hash()
                    logger.debug(f"[GRAPH] Node '{active_node}' anchored. Hash: {state.state_hash[:8]}...")

                elif active_node in self.nodes and self.nodes.get(active_node) is not None:
                    # Case handled above, just anchor
                    state.execution_path.append(active_node)
                    state.state_hash = state.compute_hash()
                    logger.debug(f"[GRAPH] Node '{active_node}' anchored. Hash: {state.state_hash[:8]}...")

                elif active_node in self.parallel_groups:
                    # Merkle Anchoring: Capture parent state before execution
                    state.parent_hash = state.state_hash
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
                        # Spawn properly named tasks for telemetry
                        wrapped_tasks = []
                        for i, t_coro in enumerate(tasks):
                            task_name = f"{active_node}:worker_{i}"
                            wrapped_tasks.append(AsyncRuntime.spawn(t_coro, name=task_name))

                        # Temporal Sandboxing: Mock System Clock
                        if state.temporal_context and state.temporal_context.is_backtest:
                            from freezegun import freeze_time

                            with freeze_time(state.temporal_context.reference_time):
                                results = await asyncio.gather(*wrapped_tasks, return_exceptions=True)
                        else:
                            results = await asyncio.gather(*wrapped_tasks, return_exceptions=True)

                        for i, res in enumerate(results):
                            if isinstance(res, Exception):
                                node_name = group_nodes[i] if i < len(group_nodes) else "unknown"
                                logger.error(f"[GRAPH] Error in parallel node {node_name}: {res}")

                    # Merkle Update: Parallel groups update the state hash once after all workers
                    state.execution_path.append(f"parallel:{active_node}")
                    state.state_hash = state.compute_hash()

                else:
                    logger.error(f"[GRAPH] Unknown flow control: {active_node}")
                    break

                # If the node didn't explicitly return a next step (or returned None),
                # check the declarative edge registry, prioritizing conditional edges.
                if next_node is None:
                    # 1. Check valid conditional edges
                    if active_node in self.conditional_edges:
                        condition_func, route_map = self.conditional_edges[active_node]
                        try:
                            route_key = condition_func(state)
                            next_node = route_map.get(route_key)
                            if not next_node:
                                logger.warning(
                                    f"[GRAPH] Condition returned '{route_key}' but no mapping found for node '{active_node}'"
                                )
                        except Exception as e:
                            logger.error(f"[GRAPH] Conditional edge logic failed for '{active_node}': {e}")

                    # 2. If no conditional match (or no condition), fall back to static edge
                    if next_node is None:
                        next_node = self.edges.get(active_node)

                active_node = next_node

            state.latencies["total_graph"] = time.time() - start_total
            logger.info(f"[GRAPH] Total cycle took {state.latencies['total_graph']:.2f}s")
        finally:
            temporal_context_var.reset(token)

        return state

    def aggregate_usage(self, state: BaseGraphState, agent_output: Any) -> None:
        r"""
        Aggregates token usage from an agent output into the global graph state.

        Args:
            state (`BaseGraphState`):
                The state object where usage statistics are accumulated.
            agent_output (`Any`):
                The output from an agent execution, which may contain 'usage' metadata.

        Returns:
            `None`
        r"""
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
