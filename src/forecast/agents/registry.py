import logging
from typing import Any, Dict, List, Optional, Union
from forecast.agents.base import Agent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Handles explicit registration and discovery of specialist agents.
    Enables modular, multi-agent reasoning swarms.
    """

class AgentRegistry:
    """
    Handles explicit registration and discovery of Lego-piece Agents.
    Supports dependency-free discovery for graph assembly.
    """
    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Union[Agent, type], name: Optional[str] = None):
        """Registers an agent (instance or class) in the registry."""
        if isinstance(agent, type):
            # If it's a class, we'll instantiate it if we can
            # but usually we want instances registered with specific configs
            agent = agent()
        
        name = name or agent.name
        self._agents[name.lower()] = agent
        logger.info(f"[REGISTRY] Registered agent: {name.upper()}")

    def get_agent(self, name: str) -> Optional[Agent]:
        """Retrieves an agent by name."""
        return self._agents.get(name.lower())

    def list_agents(self) -> List[str]:
        """Returns a list of all registered agent names."""
        return list(self._agents.keys())

    # Compatibility Aliases for legacy specialist support
    def get_specialist(self, domain: str) -> Optional[Agent]:
        return self.get_agent(domain)

# Global Singleton instance for the library
registry = AgentRegistry()
