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

r"""Tests for the caching search-tool wrapper."""

from typing import Any, Dict, List, Optional

from xrtm.forecast.core.cache import InferenceCache
from xrtm.forecast.kit.tools.caching import CachedSearchTool


class FakeSearchTool:
    name = "fake"

    def __init__(self) -> None:
        self.search_calls = 0
        self.formatted_calls = 0

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        self.search_calls += 1
        return [{"title": query, "max_results": max_results}]

    def search_formatted(self, query: str, max_results: Optional[int] = None) -> str:
        self.formatted_calls += 1
        return f"results for {query} ({max_results})"


def _cache(tmp_path) -> InferenceCache:
    return InferenceCache(db_path=str(tmp_path / "search.db"))


def test_search_is_cached(tmp_path):
    tool = FakeSearchTool()
    cached = CachedSearchTool(tool, cache=_cache(tmp_path))

    first = cached.search("inflation", max_results=3)
    second = cached.search("inflation", max_results=3)

    assert first == second
    assert tool.search_calls == 1
    assert cached.stats["hits"] == 1
    assert cached.stats["misses"] == 1


def test_different_max_results_is_a_different_key(tmp_path):
    tool = FakeSearchTool()
    cached = CachedSearchTool(tool, cache=_cache(tmp_path))

    cached.search("inflation", max_results=3)
    cached.search("inflation", max_results=5)

    assert tool.search_calls == 2


def test_formatted_results_are_cached(tmp_path):
    tool = FakeSearchTool()
    cached = CachedSearchTool(tool, cache=_cache(tmp_path))

    assert cached.search_formatted("gdp", max_results=2) == "results for gdp (2)"
    assert cached.search_formatted("gdp", max_results=2) == "results for gdp (2)"
    assert tool.formatted_calls == 1


def test_malformed_cache_entry_falls_through(tmp_path):
    tool = FakeSearchTool()
    cache = _cache(tmp_path)
    cached = CachedSearchTool(tool, cache=cache)

    key = cached._key("search", "broken", None)
    cache.set(key, "not-json")

    results = cached.search("broken")
    assert results == [{"title": "broken", "max_results": None}]
    assert tool.search_calls == 1
