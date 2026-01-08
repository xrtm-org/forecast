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
import threading
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

    This implementation includes threading locks for skill management to ensure
    stability in concurrent execution environments.

    Args:
        name (`str`, *optional*):
            The logical name of the agent. Defaults to the class name.
    """

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.skills: Dict[str, Any] = {}
        self._skills_lock = threading.Lock()

    @classmethod
    def from_config(cls, model: Optional[Any] = None, name: Optional[str] = None, **kwargs) -> "Agent":
        r"""
        Factory method to create an agent instance.

        This method provides ergonomic shortcuts for agent initialization. If a
        string is passed as the `model`, it is automatically resolved into a
        provider instance via the `ModelFactory`.

        Args:
            model (`Any`, *optional*):
                The model instance or a shortcut string (e.g. "gemini").
            name (`str`, *optional*):
                The agent's logical name.
            **kwargs:
                Additional arguments passed to the constructor.

        Returns:
            `Agent`: A fully initialized agent instance.
        """
        import inspect

        from forecast.inference.factory import ModelFactory

        # Ergonomic Shortcut: Resolve model string into a provider
        if isinstance(model, str):
            model = ModelFactory.get_provider(model)

        # Basic injection loop: if constructor takes 'model' and we have one, pass it.
        sig = inspect.signature(cls.__init__)
        if "model" in sig.parameters and model:
            return cls(model=model, name=name, **kwargs)  # type: ignore[call-arg]

        return cls(name=name, **kwargs)

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
        with self._skills_lock:
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
        with self._skills_lock:
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
            "version": "0.1.1",  # Placeholder for versioning logic
        }


__all__ = ["Agent"]
