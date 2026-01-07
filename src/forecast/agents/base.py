import abc
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from forecast.utils.parser import parse_json_markdown

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class Agent(abc.ABC):
    """
    Fundamental Lego piece of the xrtm-forecast engine. 
    Everything (LLMs, Tools, Graphs) is an Agent.
    """
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__

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
            "version": "0.1.0" # Placeholder for versioning logic
        }
