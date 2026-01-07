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
from typing import Any, Protocol, runtime_checkable


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


__all__ = ["Skill", "BaseSkill"]
