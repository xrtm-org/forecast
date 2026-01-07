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

import abc
import inspect
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class Tool(abc.ABC):
    r"""
    Abstract Base Class for all atomic actions available to agents.

    `Tool` defines the interface for deterministic Python functions that agents
    can invoke. It is designed to be compatible with modern tool-calling protocols
    (e.g., UTCP).
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        r"""The unique identifier of the tool."""
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        r"""A descriptive summary of the tool's purpose and usage."""
        pass

    @property
    @abc.abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        r"""Returns a JSON schema representing the tool's arguments."""
        pass

    @abc.abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        r"""
        Asynchronously executes the tool logic.

        Args:
            **kwargs:
                Keyword arguments matching the `parameters_schema`.

        Returns:
            `Any`: The result of the tool execution.
        """
        pass


class StrandToolWrapper(Tool):
    r"""
    An adapter for integrating tools from the Strands-Agents SDK.

    This wrapper allows tools designed for the Strands ecosystem to be used
    natively within xrtm-forecast.

    Args:
        strand_tool (`Any`):
            The Strands tool instance to wrap.
    """

    def __init__(self, strand_tool: Any):
        self._tool = strand_tool

    @property
    def name(self) -> str:
        return getattr(self._tool, "name", "unnamed_strand_tool")

    @property
    def description(self) -> str:
        return getattr(self._tool, "description", "No description provided.")

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        if hasattr(self._tool, "parameters"):
            return self._tool.parameters
        if hasattr(self._tool, "spec"):
            return self._tool.spec
        return {}

    async def run(self, **kwargs: Any) -> Any:
        try:
            if inspect.iscoroutinefunction(self._tool.fn):
                return await self._tool.fn(**kwargs)
            else:
                return self._tool.fn(**kwargs)
        except Exception as e:
            logger.error(f"Strand Tool {self.name} failed: {e}")
            return f"Error: {str(e)}"


class FunctionTool(Tool):
    r"""
    A standard wrapper for converting a Python function into a `Tool`.

    Args:
        fn (`Callable`):
            The function to wrap.
        name (`str`, *optional*):
            Overrides the function's name.
        description (`str`, *optional*):
            Overrides the function's docstring.
    """

    def __init__(self, fn: Callable, name: Optional[str] = None, description: Optional[str] = None):
        self.fn = fn
        self._name = name or fn.__name__
        self._description = description or fn.__doc__ or "No description provided."
        self._schema = self._generate_simple_schema(fn)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return self._schema

    async def run(self, **kwargs: Any) -> Any:
        if inspect.iscoroutinefunction(self.fn):
            return await self.fn(**kwargs)
        return self.fn(**kwargs)

    def _generate_simple_schema(self, fn: Callable) -> Dict[str, Any]:
        sig = inspect.signature(fn)
        properties = {}
        required = []
        for name, param in sig.parameters.items():
            properties[name] = {"type": "string"}  # Default to string for simplicity
            if param.default == inspect.Parameter.empty:
                required.append(name)
        return {"type": "object", "properties": properties, "required": required}


__all__ = ["Tool", "StrandToolWrapper", "FunctionTool"]
