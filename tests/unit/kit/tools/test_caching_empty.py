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

r"""Empty search results must not be cached (they poison the TTL window)."""

from xrtm.forecast.core.cache import InferenceCache
from xrtm.forecast.kit.tools.caching import CachedSearchTool


class _FlakyTool:
    def __init__(self):
        self.calls = 0
        self.fail = True

    def search(self, query, max_results=None):
        self.calls += 1
        return [] if self.fail else [{"title": "ok"}]

    def search_formatted(self, query, max_results=None):
        self.calls += 1
        return "No search results found." if self.fail else "formatted result"


def test_empty_search_results_are_not_cached(tmp_path):
    tool = _FlakyTool()
    cache = InferenceCache(db_path=str(tmp_path / "cache.db"), ttl_seconds=3600)
    cached = CachedSearchTool(tool, cache=cache, ttl_seconds=3600)

    assert cached.search("q") == []  # transient failure
    tool.fail = False
    assert cached.search("q") == [{"title": "ok"}]  # retried, not served a cached []
    assert tool.calls == 2

    # non-empty results are cached
    assert cached.search("q") == [{"title": "ok"}]
    assert tool.calls == 2


def test_empty_formatted_results_are_not_cached(tmp_path):
    tool = _FlakyTool()
    cache = InferenceCache(db_path=str(tmp_path / "cache.db"), ttl_seconds=3600)
    cached = CachedSearchTool(tool, cache=cache, ttl_seconds=3600)

    assert cached.search_formatted("q").startswith("No search results")
    tool.fail = False
    assert cached.search_formatted("q") == "formatted result"
    assert tool.calls == 2
