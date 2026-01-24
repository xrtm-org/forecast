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
from typing import Dict, List, Optional, Union

from xrtm.forecast.kit.agents.base import Agent

__all__ = ["AgentRegistry", "registry"]


logger = logging.getLogger(__name__)


class AgentRegistry:
    r"""
    Handles explicit registration and discovery of specialist agents.
    Enables modular, multi-agent reasoning swarms.
    r"""

    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Union[Agent, type], name: Optional[str] = None):
        r"""
        Registers an agent (instance or class) in the registry.

        If a class is provided, it is instantiated using its default constructor.
        Agents are stored using lowercase names for case-insensitive lookup.

        Args:
            agent (`Union[Agent, type]`):
                The agent instance or class to register.
            name (`str`, *optional*):
                The name to register the agent under. Defaults to `agent.name`.

        Example:
            ```python
            from xrtm.forecast.kit.agents.registry import registry
            from xrtm.forecast.kit.agents.analyst import ForecastAnalyst

            analyst = ForecastAnalyst(name="ExpertAnalyst")
            registry.register(analyst)

            # Retrieval
            agent = registry.get_agent("expertanalyst")
            ```
        r"""
        if isinstance(agent, type):
            # If it's a class, we'll instantiate it if we can
            # but usually we want instances registered with specific configs
            agent = agent()

        # Mypy safe cast
        from typing import cast

        agent_instance = cast(Agent, agent)

        name = name or agent_instance.name
        self._agents[name.lower()] = agent_instance
        logger.info(f"[REGISTRY] Registered agent: {name.upper()}")

    def get_agent(self, name: str) -> Optional[Agent]:
        r"""Retrieves an agent by name."""
        return self._agents.get(name.lower())

    def list_agents(self) -> List[str]:
        r"""Returns a list of all registered agent names."""
        return list(self._agents.keys())

    # Compatibility Aliases for legacy specialist support
    def get_specialist(self, domain: str) -> Optional[Agent]:
        return self.get_agent(domain)


# Global Singleton instance for the library
registry = AgentRegistry()
