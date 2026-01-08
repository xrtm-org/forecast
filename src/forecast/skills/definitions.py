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
from typing import Any, Callable, Optional, Protocol, runtime_checkable


@runtime_checkable
class Skill(Protocol):
    r"""
    A structural protocol defining the interface for high-level agent behaviors.

    Skills represent complex, often stateful capabilities that an agent can possess.
    Unlike atomic Tools, Skills typically orchestrate multiple tools or sub-processes
    to achieve a broader goal (e.g., "Web Research" consists of searching,
    crawling, and summarizing).
    """

    @property
    def name(self) -> str:
        r"""The unique identifier for the skill."""
        ...

    @property
    def description(self) -> str:
        r"""A detailed summary of what the skill does and when to use it."""
        ...

    async def execute(self, **kwargs: Any) -> Any:
        r"""
        Executes the skill's logic using the provided context.

        Args:
            **kwargs:
                Arbitrary keyword arguments representing the skill's parameters
                (e.g., `query="market trends"`).

        Returns:
            `Any`: The result of the skill execution.
        """
        ...


class BaseSkill(abc.ABC):
    r"""
    Abstract base class providing a skeletal implementation for the `Skill` protocol.

    Developers implementing new skills should inherit from this class to ensure
    compatibility with the platform's agent and registry systems.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        pass

    @abc.abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        pass


class FunctionalSkill(BaseSkill):
    r"""
    A wrapper class that converts a Python function into a `Skill`.

    This class enables functional programming patterns within the engine by
    providing a standard `Skill` interface for naked functions.
    """

    def __init__(self, func: Callable, name: str, description: str):
        self._func = func
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def execute(self, **kwargs: Any) -> Any:
        return await self._func(**kwargs)


def skill(name: str, description: Optional[str] = None):
    r"""
    Decorator to convert an async function into a `Skill`.

    The decorated function is automatically wrapped in a `FunctionalSkill` and
    can be registered with the platform's tool registry.

    Args:
        name (`str`):
            The unique identifier for the skill.
        description (`str`, *optional*):
            A summary of the skill's purpose. If omitted, the function's
            docstring is used.

    Returns:
        `Callable`: The decorator function.
    """

    def decorator(func):
        desc = description or func.__doc__ or "No description provided."
        functional_skill = FunctionalSkill(func, name, desc)

        # Auto-register with the global registry if available
        # We perform a lazy import to avoid circular dependencies
        try:
            from forecast.tools.registry import tool_registry

            tool_registry.register_skill(functional_skill)
        except (ImportError, AttributeError):
            pass

        return functional_skill

    return decorator


__all__ = ["Skill", "BaseSkill", "FunctionalSkill", "skill"]
