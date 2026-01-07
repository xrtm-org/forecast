import logging
import time
from typing import Any, Callable, Dict, Optional

from forecast.schemas.graph import BaseGraphState

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Manages complex agent workflows using a state machine.
    Domain-agnostic engine that processes a GraphState through a node registry.
    """

    def __init__(self, max_cycles: int = 3):
        self.max_cycles = max_cycles
        # Registry of nodes (functions) that process the state
        # format: {"node_name": callable}
        self.nodes: Dict[str, Callable] = {}

    def register_node(self, name: str, func: Callable):
        """Registers a processing node in the graph."""
        self.nodes[name] = func

    async def run(
        self,
        state: BaseGraphState,
        entry_node: str = "ingestion",
        on_progress: Optional[Callable] = None,
        stopwatch: Optional[Any] = None,
    ) -> BaseGraphState:
        """
        Orchestrates the execution of the state-machine nodes.
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

    def aggregate_usage(self, state: BaseGraphState, agent_output: Any):
        """Standardized usage tracking from Pydantic models or dicts."""
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
