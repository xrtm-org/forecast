import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """
    Abstract interface for Vector Databases.
    Standardizes retrieval and storage for RAG.
    """

    @abstractmethod
    def upsert(self, ids: List[str], documents: List[str], metadatas: List[dict]):
        pass

    @abstractmethod
    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, Any]:
        pass


class MemoryRegistry:
    """
    Registry for Vector Store providers.
    Enables swapping vector DB backends at runtime.
    """

    _providers: Dict[str, BaseVectorStore] = {}

    @classmethod
    def register_provider(cls, name: str, provider: BaseVectorStore):
        cls._providers[name.upper()] = provider
        logger.info(f"[MEMORY] Registered Vector Store: {name}")

    @classmethod
    def get_provider(cls, name: str) -> Optional[BaseVectorStore]:
        return cls._providers.get(name.upper())

    @classmethod
    def list_providers(cls) -> List[str]:
        return list(cls._providers.keys())
