import abc
import logging
from typing import Any, Dict, Optional, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class Agent(abc.ABC):
    """
    Fundamental Lego piece of the xrtm-forecast engine.
    Everything (LLMs, Tools, Graphs) is an Agent.
    """
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.skills: Dict[str, Any] = {}

    def add_skill(self, skill: Any) -> None:
        """Equips the agent with a new skill."""
        self.skills[skill.name] = skill
        logger.debug(f"Agent {self.name} equipped with skill: {skill.name}")

    def get_skill(self, name: str) -> Optional[Any]:
        """Retrieves a skill by name."""
        return self.skills.get(name)

    @abc.abstractmethod
    async def run(self, input_data: Any, **kwargs) -> Any:
        """
        Asynchronous execution of the agent's logic.
        Ideally uses Pydantic models for input/output.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Returns metadata about the agent for structural tracing."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "version": "0.1.1" # Placeholder for versioning logic
        }
