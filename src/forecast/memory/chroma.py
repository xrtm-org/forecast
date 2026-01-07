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
import os
from typing import Any, Dict, List, Optional

from forecast.memory.base import BaseVectorStore

logger = logging.getLogger(__name__)


class ChromaProvider(BaseVectorStore):
    """
    Standard implementation of ChromaDB for the forecast library.
    """

    def __init__(self, collection_name: str, persist_directory: Optional[str] = None):
        self.collection_name = collection_name
        self.persist_directory = persist_directory or "./data/chroma_db"
        self.collection = None
        self._initialize()

    def _initialize(self):
        try:
            import chromadb

            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"[CHROMA] Failed to initialize: {e}")

    def upsert(self, ids: List[str], documents: List[str], metadatas: List[dict]):
        if self.collection:
            try:
                self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            except Exception as e:
                logger.error(f"[CHROMA] Upsert failed: {e}")

    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, Any]:
        if self.collection:
            try:
                return self.collection.query(query_texts=query_texts, n_results=n_results)
            except Exception as e:
                logger.error(f"[CHROMA] Query failed: {e}")
        return {"documents": [[]], "metadatas": [[]]}
