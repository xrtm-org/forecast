import inspect
from typing import Any, Callable, Optional

from forecast.agents.base import Agent


class ToolAgent(Agent):
    """
    Agent that wraps a deterministic Python function.
    Treats a 'Tool' as a first-class agent.
    """
    def __init__(self, fn: Callable, name: Optional[str] = None):
        super().__init__(name or fn.__name__)
        self.fn = fn

    async def run(self, input_data: Any, **kwargs) -> Any:
        """
        Executes the wrapped function.
        If input_data is a Pydantic model, it passes it as kwargs or a single arg.
        """
        # Handling for both async and sync functions
        if inspect.iscoroutinefunction(self.fn):
            if isinstance(input_data, dict):
                return await self.fn(**input_data)
            return await self.fn(input_data)
        else:
            if isinstance(input_data, dict):
                return self.fn(**input_data)
            return self.fn(input_data)
