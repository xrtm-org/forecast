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
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    r"""
    Abstract interface for managing vector embeddings and performing semantic search.

    `BaseVectorStore` provides a unified contract for different Vector Database
    backends (e.g., Chroma, Pinecone, FAISS), enabling seamless RAG (Retrieval-Augmented
    Generation) workflows.
    """

    @abstractmethod
    def upsert(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        r"""
        Adds or updates documents in the vector store.

        Args:
            ids (`List[str]`):
                Unique identifiers for each document.
            documents (`List[str]`):
                The raw text content to be embedded and stored.
            metadatas (`List[Dict[str, Any]]`):
                Key-value pairs associated with each document for filtering.
        """
        pass

    @abstractmethod
    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, Any]:
        r"""
        Performs a semantic search for the most relevant documents.

        Args:
            query_texts (`List[str]`):
                The natural language queries used to retrieve matching documents.
            n_results (`int`, *optional*, defaults to `3`):
                The number of results to return per query.

        Returns:
            `Dict[str, Any]`: The raw response from the vector store containing documents and scores.
        """
        pass


class MemoryRegistry:
    r"""
    A central registry for managing and swapping Vector Store providers at runtime.
    """

    _providers: Dict[str, BaseVectorStore] = {}

    @classmethod
    def register_provider(cls, name: str, provider: BaseVectorStore):
        r"""Registers a new vector store implementation."""
        cls._providers[name.upper()] = provider
        logger.info(f"[MEMORY] Registered Vector Store: {name}")

    @classmethod
    def get_provider(cls, name: str) -> Optional[BaseVectorStore]:
        r"""Retrieves a registered vector store by name."""
        return cls._providers.get(name.upper())

    @classmethod
    def list_providers(cls) -> List[str]:
        r"""Returns names of all registered providers."""
        return list(cls._providers.keys())


__all__ = ["BaseVectorStore", "MemoryRegistry"]
