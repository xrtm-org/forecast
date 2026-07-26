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

r"""Web search skill for agents.

Uses Tavily Search API to give agents real-time web search capability.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from xrtm.forecast.kit.skills.definitions import BaseSkill
from xrtm.forecast.kit.tools.search import TavilySearchTool

logger = logging.getLogger(__name__)


class WebSearchSkill(BaseSkill):
    r"""Agent skill for web search via Tavily.

    Equip a ``ForecastingAnalyst`` (or any agent) with this skill to
    enable real-time web research during forecast generation.

    Example:
        >>> analyst = ForecastingAnalyst(model=provider, name="researcher")
        >>> analyst.add_skill(WebSearchSkill())
        >>> forecast = await analyst.run(question)
    """

    name: str = "web_search"
    description: str = "Search the web for current information and news."

    def __init__(self, search_tool: TavilySearchTool | None = None):
        self._search_tool = search_tool or TavilySearchTool()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        r"""Execute a web search and return structured results.

        Args:
            query: The search query string.
            max_results: Optional max results (default 5).

        Returns:
            Dict with keys: ``formatted`` (text for LLM prompts),
            ``query``, ``results_count``, ``sources``, ``search_time_ms``.
        """
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results")
        start = time.perf_counter()
        results = self._search_tool.search(query, max_results=max_results)
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        sources = [r.get("url", "") for r in results if r.get("url")]
        formatted = self._search_tool.search_formatted(query, max_results=max_results)
        return {
            "formatted": formatted,
            "query": query,
            "results_count": len(results),
            "sources": sources,
            "search_time_ms": elapsed_ms,
        }


__all__ = ["WebSearchSkill"]
