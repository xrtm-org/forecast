import logging
from typing import Any, Callable, Dict, List, Optional

from forecast.tools.base import FunctionTool, StrandToolWrapper, Tool

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Central repository for all tools available to the forecasting engine.
    Follows the same manifest pattern as AgentRegistry.
    """
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        """Registers a Tool instance."""
        if tool.name in self._tools:
            logger.warning(f"Overwriting tool: {tool.name}")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def register_fn(self, fn: Callable, name: Optional[str] = None, description: Optional[str] = None):
        """Convenience method to register a simple function as a tool."""
        tool = FunctionTool(fn, name=name, description=description)
        self.register_tool(tool)

    def register_strand_tool(self, strand_tool: Any):
        """Wrapper to register a Strand-Agents tool."""
        tool = StrandToolWrapper(strand_tool)
        self.register_tool(tool)

    def get_tool(self, name: str) -> Optional[Tool]:
        """Retrieves a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """Lists names of all registered tools."""
        return list(self._tools.keys())

    def get_all_specs(self) -> List[Dict[str, Any]]:
        """Returns JSON schemas for all registered tools (useful for LLM function calling)."""
        specs = []
        for tool in self._tools.values():
            specs.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters_schema
            })
        return specs

# Global singleton for easy access across the library
tool_registry = ToolRegistry()
