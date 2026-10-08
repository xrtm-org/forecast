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

r"""Caching wrapper for search tools.

Caches deterministic tool calls (search results, formatted snippets) in the
SQLite-backed :class:`InferenceCache` with an optional TTL. This cuts external
API calls and makes backtests reproducible: the same query returns the same
evidence without re-hitting the network.

Example:
    >>> from xrtm.forecast.kit.tools.caching import CachedSearchTool
    >>> cached = CachedSearchTool(my_search_tool, ttl_seconds=3600)  # doctest: +SKIP
    >>> cached.search("inflation expectations", max_results=5)  # doctest: +SKIP
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from xrtm.forecast.core.cache import InferenceCache

logger = logging.getLogger(__name__)

__all__ = ["CachedSearchTool"]


class CachedSearchTool:
    r"""Wrap a search tool with a persistent, TTL'd cache.

    Args:
        tool: Object implementing ``search(query, max_results=...)`` and/or
            ``search_formatted(query, max_results=...)``.
        cache: Optional :class:`InferenceCache` (defaults to the standard
            ``.cache/inference.db`` with ``ttl_seconds``).
        ttl_seconds: Cache TTL for this tool's entries (default 24 h).

    Attributes:
        stats: Hit/miss counters plus underlying cache statistics.
    """

    def __init__(self, tool: Any, cache: Optional[InferenceCache] = None, ttl_seconds: int = 86_400):
        self.tool = tool
        self.ttl_seconds = ttl_seconds
        self.cache = cache or InferenceCache(ttl_seconds=ttl_seconds)
        self._hits = 0
        self._misses = 0

    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        r"""Return cached search results, falling back to the wrapped tool."""
        key = self._key("search", query, max_results)
        cached = self.cache.get(key)
        if cached is not None:
            try:
                self._hits += 1
                return json.loads(cached)
            except json.JSONDecodeError:
                logger.warning("Discarding malformed cached search payload for %r", query)

        self._misses += 1
        results = self.tool.search(query, max_results=max_results)
        # Never cache empty results: a transient failure would otherwise be
        # served as a cache hit for the whole TTL.
        if results:
            self.cache.set(key, json.dumps(results, default=str))
        return results

    def search_formatted(self, query: str, max_results: Optional[int] = None) -> str:
        r"""Return cached formatted results, falling back to the wrapped tool."""
        key = self._key("formatted", query, max_results)
        cached = self.cache.get(key)
        if cached is not None:
            self._hits += 1
            return cached

        self._misses += 1
        formatted = self.tool.search_formatted(query, max_results=max_results)
        if formatted and not formatted.startswith("No search results"):
            self.cache.set(key, formatted)
        return formatted

    def _key(self, kind: str, query: str, max_results: Optional[int]) -> str:
        name = getattr(self.tool, "name", None) or type(self.tool).__name__
        return self.cache.compute_key(f"tool:{name}:{kind}", query, max_results=max_results)

    @property
    def stats(self) -> Dict[str, Any]:
        r"""Hit/miss counters plus underlying cache statistics."""
        base: Dict[str, Any] = {}
        if hasattr(self.cache, "stats"):
            try:
                base = self.cache.stats()
            except Exception:  # noqa: BLE001 - stats must never break a caller
                base = {}
        return {**base, "hits": self._hits, "misses": self._misses, "ttl_seconds": self.ttl_seconds}
