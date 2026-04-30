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

r"""ChromaDB vector memory store.

Concrete implementation of the memory store interface using
ChromaDB for persistent vector similarity search, supporting
episodic memory retrieval for agent reasoning.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from xrtm.forecast.kit.memory.base import BaseVectorStore

logger = logging.getLogger(__name__)

__all__ = ["ChromaProvider"]


class ChromaProvider(BaseVectorStore):
    r"""
    Standard implementation of ChromaDB for the forecast library.
    r"""

    def __init__(self, collection_name: str, persist_directory: Optional[str] = None):
        self.collection_name = collection_name
        self.persist_directory = str(Path(persist_directory or "./data/chroma_db").expanduser().resolve(strict=False))
        self.client: Any = None
        self.collection: Any = None
        self._closed = False
        self._initialize()

    def _initialize(self):
        if self._closed:
            raise RuntimeError("ChromaProvider is closed")
        try:
            import chromadb

            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"[CHROMA] Failed to initialize: {e}")

    def _ensure_open(self) -> bool:
        if self._closed:
            raise RuntimeError("ChromaProvider is closed")
        return self.collection is not None

    def upsert(self, ids: List[str], documents: List[str], metadatas: List[dict]):
        if self._ensure_open():
            try:
                self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            except Exception as e:
                logger.error(f"[CHROMA] Upsert failed: {e}")

    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, Any]:
        if self._ensure_open():
            try:
                return self.collection.query(query_texts=query_texts, n_results=n_results)
            except Exception as e:
                logger.error(f"[CHROMA] Query failed: {e}")
        return {"documents": [[]], "metadatas": [[]]}

    def reset_collection(self) -> None:
        r"""Delete and recreate the configured collection."""
        if not self._ensure_open() or self.client is None:
            return
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception as e:
            logger.debug(f"[CHROMA] Collection reset delete skipped: {e}")
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )

    def close(self) -> None:
        r"""Release references to the Chroma client and collection."""
        self.collection = None
        self.client = None
        self._closed = True
