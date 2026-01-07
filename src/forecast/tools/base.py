import abc
import inspect
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

class Tool(abc.ABC):
    """
    Abstract Base Class for all tools available to agents.
    Designed to be compatible with UTCP (Universal Tool Calling Protocol) standards.
    """
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """Returns JSON schema for tool arguments."""
        pass

    @abc.abstractmethod
    async def run(self, **kwargs) -> Any:
        """Asynchronous execution logic."""
        pass

class StrandToolWrapper(Tool):
    """
    Adapter to allow Strands-Agents SDK tools to be used natively within xrtm-forecast.
    """
    def __init__(self, strand_tool: Any):
        """
        Wraps a tool created with @strands.tool or the Strand Tool class.
        Expects the object to have .name, .description, and .spec/schema.
        """
        self._tool = strand_tool

    @property
    def name(self) -> str:
        # Strands tools usually expose .name
        return getattr(self._tool, "name", "unnamed_strand_tool")

    @property
    def description(self) -> str:
        return getattr(self._tool, "description", "No description provided.")

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        # Handle different versions of tool specs
        if hasattr(self._tool, "parameters"):
            return self._tool.parameters
        if hasattr(self._tool, "spec"):
            return self._tool.spec
        return {}

    async def run(self, **kwargs) -> Any:
        # Strands tools are typically async or threadable
        # Direct call to the underlying tool function
        try:
            if inspect.iscoroutinefunction(self._tool.fn):
                return await self._tool.fn(**kwargs)
            else:
                return self._tool.fn(**kwargs)
        except Exception as e:
            logger.error(f"Strand Tool {self.name} failed: {e}")
            return f"Error: {str(e)}"

class FunctionTool(Tool):
    """
    Standard tool created from a simple Python function.
    """
    def __init__(self, fn: Callable, name: Optional[str] = None, description: Optional[str] = None):
        self.fn = fn
        self._name = name or fn.__name__
        self._description = description or fn.__doc__ or "No description provided."
        self._schema = self._generate_simple_schema(fn)

    @property
    def name(self) -> str: return self._name
    @property
    def description(self) -> str: return self._description
    @property
    def parameters_schema(self) -> Dict[str, Any]: return self._schema

    async def run(self, **kwargs) -> Any:
        if inspect.iscoroutinefunction(self.fn):
            return await self.fn(**kwargs)
        return self.fn(**kwargs)

    def _generate_simple_schema(self, fn: Callable) -> Dict[str, Any]:
        # Minimal automated schema generation
        sig = inspect.signature(fn)
        properties = {}
        required = []
        for name, param in sig.parameters.items():
            properties[name] = {"type": "string"} # Default to string for simplicity
            if param.default == inspect.Parameter.empty:
                required.append(name)
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
