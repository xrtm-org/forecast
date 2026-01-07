import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

from forecast.agents.base import Agent
from forecast.inference.base import InferenceProvider
from forecast.tools.registry import tool_registry
from forecast.utils.parser import parse_json_markdown

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

class LLMAgent(Agent):
    """
    Agent that utilizes an LLM (InferenceProvider) for reasoning.
    """
    def __init__(self, model: InferenceProvider, name: Optional[str] = None):
        super().__init__(name)
        self.model = model

    def get_tools(self, tool_names: Optional[List[str]] = None) -> List[Any]:
        """
        Retrieves tool instances from the global registry.
        If tool_names is None, returns all registered tools.
        """
        if tool_names is None:
            # Return all wrapped tool objects
            return [tool_registry.get_tool(name) for name in tool_registry.list_tools()]

        tools = []
        for name in tool_names:
            tool = tool_registry.get_tool(name)
            if tool:
                tools.append(tool)
        return tools

    def parse_output(
        self, text: str, schema: Optional[Type[T]] = None, default: Any = None
    ) -> Union[T, Dict[str, Any]]:
        """Parses LLM text into a Pydantic model or dict."""
        parsed = parse_json_markdown(text)
        if parsed is None:
            return default if default is not None else {}

        if schema and isinstance(parsed, dict):
            try:
                # Filter out keys not in schema to prevent validation errors
                valid_fields = schema.model_fields.keys()
                filtered = {k: v for k, v in parsed.items() if k in valid_fields}
                return schema(**filtered)
            except Exception as e:
                logger.warning(f"Schema validation failed: {e}")
                return default if default is not None else parsed
        return parsed

    async def run(self, input_data: Any, **kwargs) -> Any:
        # LLMAgents will typically override this with specific prompting logic
        raise NotImplementedError("LLMAgent subclasses must implement run")
