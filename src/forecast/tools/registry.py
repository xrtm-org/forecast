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
from typing import Any, Callable, Dict, List, Optional

from forecast.tools.base import FunctionTool, StrandToolWrapper, Tool
from forecast.tools.config import ToolConfig

logger = logging.getLogger(__name__)


class ToolRegistry:
    r"""
    A central repository for discovering and invoking atomic tools.

    `ToolRegistry` simplifies agent interaction with Python functions by managing
    their metadata and providing standardized access to their JSON schemas for
    LLM function calling.
    """

    def __init__(self, config: Optional[ToolConfig] = None):
        self.config = config or ToolConfig()
        self._tools: Dict[str, Tool] = {}
        self._skills: Dict[str, Any] = {}

    def register_tool(self, tool: Tool):
        r"""
        Registers a specialized `Tool` instance.

        Args:
            tool (`Tool`):
                The tool object to register.
        """
        if tool.name in self._tools:
            logger.warning(f"Overwriting tool: {tool.name}")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def register_skill(self, skill: Any):
        r"""
        Registers a high-level `Skill` instance.

        Args:
            skill (`Skill`):
                The skill object to register.
        """
        if skill.name in self._skills:
            logger.warning(f"Overwriting skill: {skill.name}")
        self._skills[skill.name] = skill
        logger.debug(f"Registered skill: {skill.name}")

    def register_fn(self, fn: Callable, name: Optional[str] = None, description: Optional[str] = None):
        r"""
        Convenience method to register a naked Python function as a tool.

        Args:
            fn (`Callable`):
                The function to wrap.
            name (`str`, *optional*):
                Override for the function name.
            description (`str`, *optional*):
                Override for the function docstring.
        """
        tool = FunctionTool(fn, name=name, description=description)
        self.register_tool(tool)

    def register_strand_tool(self, strand_tool: Any):
        r"""Registers a tool from the Strands-Agents SDK."""
        tool = StrandToolWrapper(strand_tool)
        self.register_tool(tool)

    def get_tool(self, name: str) -> Optional[Tool]:
        r"""Retrieves a registered tool by name."""
        return self._tools.get(name)

    def get_skill(self, name: str) -> Optional[Any]:
        r"""Retrieves a registered skill by name."""
        return self._skills.get(name)

    def list_tools(self) -> List[str]:
        r"""Returns a list of all registered tool names."""
        return list(self._tools.keys())

    def list_skills(self) -> List[str]:
        r"""Returns a list of all registered skill names."""
        return list(self._skills.keys())

    def list_available(self) -> List[Dict[str, Any]]:
        r"""
        Returns metadata for all available tools and skills.

        Returns:
            `List[Dict[str, Any]]`: A list of metadata dictionaries.
        """
        available = []
        for name, tool in self._tools.items():
            available.append({"name": name, "type": "tool", "description": tool.description})
        for name, skill in self._skills.items():
            available.append({"name": name, "type": "skill", "description": skill.description})
        return available

    def get_all_specs(self) -> List[Dict[str, Any]]:
        r"""
        Generates functional specifications for all registered tools.

        Returns:
            `List[Dict[str, Any]]`: A list of dictionaries matching LLM tool-calling formats.
        """
        specs = []
        for tool in self._tools.values():
            specs.append({"name": tool.name, "description": tool.description, "parameters": tool.parameters_schema})
        return specs


# Global singleton for easy access across the library
tool_registry = ToolRegistry()

__all__ = ["ToolRegistry", "tool_registry"]
