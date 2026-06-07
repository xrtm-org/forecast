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

r"""Tavily web search tool.

Lightweight wrapper around the Tavily Search API for use by agents.
Requires ``TAVILY_API_KEY`` or ``TVLY_DEV_KEY`` environment variable.
Free tier: 1,000 queries/month. Sign up at https://tavily.com.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class TavilySearchTool:
    r"""Atomic web search via Tavily API.

    Args:
        api_key: Tavily API key. Defaults to ``TAVILY_API_KEY`` or
            ``TVLY_DEV_KEY`` env var.
        max_results: Maximum results per query (default 5).

    Example:
        >>> tool = TavilySearchTool()
        >>> results = tool.search("latest Fed interest rate decision")
        >>> for r in results:
        ...     print(r["title"])
    """

    def __init__(self, api_key: str | None = None, max_results: int = 5):
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY") or os.environ.get("TVLY_DEV_KEY")
        self.max_results = max_results

    def search(self, query: str, max_results: int | None = None) -> list[dict[str, Any]]:
        r"""Execute a web search query.

        Args:
            query: The search query string.
            max_results: Override default max_results.

        Returns:
            List of result dicts with keys: ``title``, ``url``, ``content``, ``score``.
        """
        if not self.api_key:
            raise ValueError(
                "Tavily API key not set. Set TAVILY_API_KEY or TVLY_DEV_KEY "
                "environment variable. Get a free key at https://tavily.com"
            )

        payload = json.dumps({
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results or self.max_results,
        }).encode("utf-8")

        req = urllib.request.Request(
            TAVILY_SEARCH_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", [])
        except Exception as exc:
            logger.error(f"Tavily search failed: {exc}")
            return []

    def search_formatted(self, query: str, max_results: int | None = None) -> str:
        r"""Search and return results as a formatted text block.

        Useful for injecting search results into LLM prompts.
        """
        results = self.search(query, max_results=max_results)
        if not results:
            return "No search results found."

        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] {r.get('title', 'Untitled')}")
            lines.append(f"    URL: {r.get('url', 'N/A')}")
            content = r.get("content", "")
            if content:
                lines.append(f"    {content[:300]}")
            lines.append("")
        return "\n".join(lines)


__all__ = ["TavilySearchTool"]
