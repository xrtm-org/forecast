import abc
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Skill(Protocol):
    """
    Protocol for high-level behaviors that agents can perform.
    Skills typically orchestrate one or more Tools.
    """
    @property
    def name(self) -> str:
        """Name of the skill."""
        ...

    @property
    def description(self) -> str:
        """Detailed description of what the skill does."""
        ...

    async def execute(self, **kwargs: Any) -> Any:
        """
        Executes the skill logic.
        """
        ...

class BaseSkill(abc.ABC):
    """
    Base class for implementing Skills.
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
