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
import logging
from typing import Any, Dict, Optional, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class Agent(abc.ABC):
    r"""
    The fundamental building block of the xrtm-forecast engine.

    Everything in the platform—including LLMs, Tools, and entire Graphs—inherits from
    the `Agent` base class. This allows for extreme modularity and recursion, where
    a complex pipeline can be treated as a single agent within a larger graph.

    Args:
        name (`str`, *optional*):
            The logical name of the agent. Defaults to the class name.
    """
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.skills: Dict[str, Any] = {}

    def add_skill(self, skill: Any) -> None:
        r"""
        Equips the agent with a new skill, allowing it to perform specialized actions.

        Args:
            skill (`Any`):
                The skill instance to equip. Must have a `name` attribute.

        Example:
            ```python
            >>> from forecast.agents.base import Agent
            >>> agent = Agent(name="Researcher")
            >>> agent.add_skill(web_search_skill)
            ```
        """
        self.skills[skill.name] = skill
        logger.debug(f"Agent {self.name} equipped with skill: {skill.name}")

    def get_skill(self, name: str) -> Optional[Any]:
        r"""
        Retrieves an equipped skill by its name.

        Args:
            name (`str`):
                The unique identifier of the skill to retrieve.

        Returns:
            `Optional[Any]`: The skill instance if found, else `None`.
        """
        return self.skills.get(name)

    @abc.abstractmethod
    async def run(self, input_data: Any, **kwargs) -> Any:
        r"""
        The core execution logic of the agent.

        This method must be implemented by all subclasses. It typically involves
        processing input data through an LLM, a tool, or a nested graph.

        Args:
            input_data (`Any`):
                The primary input for the agent. Type depends on the implementation.
            **kwargs:
                Additional execution parameters.

        Returns:
            `Any`: The result of the agent's execution.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        r"""
        Returns structural metadata about the agent for tracing and auditing.

        Returns:
            `Dict[str, Any]`: A dictionary containing 'name', 'type', and 'version'.
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "version": "0.1.1" # Placeholder for versioning logic
        }


__all__ = ["Agent"]
