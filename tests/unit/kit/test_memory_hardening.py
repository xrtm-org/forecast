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

from types import ModuleType

import pytest

from xrtm.forecast.kit.memory import Memory, MemoryRegistry
from xrtm.forecast.providers.memory.chroma_store import ChromaProvider


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[str, str] = {}
        self.metadatas: dict[str, dict] = {}

    def upsert(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> None:
        for item_id, document, metadata in zip(ids, documents, metadatas):
            self.documents[item_id] = document
            self.metadatas[item_id] = metadata

    def query(self, query_texts: list[str], n_results: int = 3) -> dict:
        return {
            "documents": [list(self.documents.values())[:n_results]],
            "metadatas": [list(self.metadatas.values())[:n_results]],
        }


class FakePersistentClient:
    instances: list["FakePersistentClient"] = []

    def __init__(self, path: str) -> None:
        self.path = path
        self.collections: dict[str, FakeCollection] = {}
        self.__class__.instances.append(self)

    def get_or_create_collection(self, name: str, metadata: dict) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection())

    def delete_collection(self, name: str) -> None:
        self.collections.pop(name, None)


@pytest.fixture(autouse=True)
def fake_chromadb(monkeypatch):
    module = ModuleType("chromadb")
    module.PersistentClient = FakePersistentClient  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "chromadb", module)
    FakePersistentClient.instances.clear()
    MemoryRegistry.clear(close=True)
    yield
    MemoryRegistry.clear(close=True)


def test_memory_reuses_chroma_only_for_same_directory_and_collection(tmp_path):
    persist_directory = str(tmp_path / "chroma")

    first = Memory("events", persist_directory=persist_directory)
    same_key = Memory("events", persist_directory=persist_directory)
    different_collection = Memory("claims", persist_directory=persist_directory)
    different_directory = Memory("events", persist_directory=str(tmp_path / "other"))
    different_case_directory = Memory("events", persist_directory=str(tmp_path / "CHROMA"))

    assert first.provider is same_key.provider
    assert first.provider is not different_collection.provider
    assert first.provider is not different_directory.provider
    assert first.provider is not different_case_directory.provider


def test_chroma_reset_and_close_have_explicit_semantics(tmp_path):
    provider = ChromaProvider("events", persist_directory=str(tmp_path / "chroma"))
    provider.upsert(ids=["1"], documents=["doc"], metadatas=[{"kind": "test"}])
    assert provider.query(["doc"])["documents"] == [["doc"]]

    provider.reset_collection()
    assert provider.query(["doc"])["documents"] == [[]]

    provider.close()
    with pytest.raises(RuntimeError, match="closed"):
        provider.query(["doc"])


def test_memory_close_clears_chroma_alias(tmp_path):
    memory = Memory("events", persist_directory=str(tmp_path / "chroma"))

    assert MemoryRegistry.get_provider("CHROMA") is memory.provider
    memory.close()

    assert MemoryRegistry.get_provider("CHROMA") is None
