from typing import Any, Optional

from forecast.agents.base import Agent
from forecast.graph.orchestrator import Orchestrator
from forecast.schemas.graph import BaseGraphState


class GraphAgent(Agent):
    """
    Agent that encapsulates a sub-graph (Orchestrator).
    Enables 'Composite Nodes' where an agent internally runs a whole pipeline.
    """
    def __init__(self, orchestrator: Orchestrator, entry_node: str, name: Optional[str] = None):
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

        await self.orchestrator.run(state, entry_node=self.entry_node)

        # Return the final context or a specific output if defined in state
        return state.context.get("output", state.context)
