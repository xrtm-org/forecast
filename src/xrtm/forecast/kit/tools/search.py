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

r"""Web search tools.

``TavilySearchTool`` (Tavily API) and ``DeepSeekSearchTool`` (DeepSeek's
in-house Search API, ¥5 / 1,000 successful requests, free until 2026-11-01)
for use by agents.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Optional

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
DEEPSEEK_SEARCH_URL = "https://api.deepseek.com/v1/tools/search"


def _format_results(results: list[dict[str, Any]], limit: int) -> str:
    r"""Render results as a prompt-ready text block."""
    if not results:
        return "No search results found."
    lines = []
    for index, result in enumerate(results, 1):
        lines.append(f"[{index}] {result.get('title', 'Untitled')}")
        lines.append(f"    URL: {result.get('url', 'N/A')}")
        content = result.get("content", "")
        if content:
            lines.append(f"    {str(content)[:limit]}")
        lines.append("")
    return "\n".join(lines)


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
        return _format_results(self.search(query, max_results=max_results), 300)


class DeepSeekSearchTool:
    r"""Web search via DeepSeek's in-house Search API.

    Cheap, structured, AI-oriented results: ``POST /v1/tools/search`` returns
    titles, URLs and 600–800 char ``summary`` fields written for models.
    Billed at ¥5 per 1,000 **successful** requests (non-empty results only);
    free until 2026-11-01.

    Args:
        api_key: DeepSeek API key. Defaults to ``DEEPSEEK_API_KEY``.
        base_url: API base URL (default ``https://api.deepseek.com``).
        max_results: Results per query, 1–50 (default 5).
        timeout: Request timeout in seconds (default 20).

    Example:
        >>> tool = DeepSeekSearchTool()
        >>> results = tool.search("latest Fed interest rate decision")
        >>> for r in results:
        ...     print(r["title"], r["url"])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        max_results: int = 5,
        timeout: float = 20.0,
    ):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.max_results = max(1, min(int(max_results), 50))
        self.timeout = timeout

    def search(self, query: str, max_results: int | None = None) -> list[dict[str, Any]]:
        r"""Execute a web search query.

        Returns:
            List of dicts with keys: ``title``, ``url``, ``content``, ``date``.
        """
        query = (query or "").strip()
        if not query or not self.api_key:
            return []
        payload = {
            "query": query[:128],
            "count": min(max(int(max_results or self.max_results), 1), 50),
            "need_content": False,
        }
        for attempt in range(2):
            try:
                request = urllib.request.Request(
                    DEEPSEEK_SEARCH_URL,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                items = data.get("results") if isinstance(data, dict) else None
                return [
                    {
                        "title": str(item.get("title") or "Untitled"),
                        "url": str(item.get("url") or ""),
                        "content": str(item.get("summary") or item.get("snippet") or ""),
                        "date": item.get("date"),
                    }
                    for item in (items or [])
                ]
            except urllib.error.HTTPError as exc:
                # 408/429/5xx are transient; other 4xx will fail again.
                if exc.code in (408, 429, 500, 502, 503, 504) and attempt == 0:
                    time.sleep(1.0)
                    continue
                logger.warning("DeepSeek search failed (HTTP %s)", exc.code)
                return []
            except Exception as exc:  # noqa: BLE001 - search must never break a forecast
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                logger.warning("DeepSeek search failed: %s", exc)
                return []
        return []

    def search_formatted(self, query: str, max_results: int | None = None) -> str:
        r"""Search and return results as a formatted text block."""
        return _format_results(self.search(query, max_results=max_results), 700)


__all__ = ["DeepSeekSearchTool", "TavilySearchTool"]
