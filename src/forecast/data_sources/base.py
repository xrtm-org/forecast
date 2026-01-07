import abc
from typing import List, Optional

from forecast.schemas.forecast import ForecastQuestion


class DataSource(abc.ABC):
    """
    Abstract interface for retrieving forecast questions.
    """
    @abc.abstractmethod
    async def fetch_questions(self, query: Optional[str] = None, limit: int = 5) -> List[ForecastQuestion]:
        """
        Retrieves a list of forecast questions based on a query or latest active markets.
        """
        pass

    @abc.abstractmethod
    async def get_question_by_id(self, question_id: str) -> Optional[ForecastQuestion]:
        """
        Retrieves a specific forecast question by its unique identifier.
        """
        pass
