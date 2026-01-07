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

from typing import Any, Optional

from forecast.skills.definitions import BaseSkill
from forecast.tools.base import Tool
from forecast.tools.search import TavilySearchTool


class WebSearchSkill(BaseSkill):
    r"""
    A Skill for gathering and synthesizing information from the open web.

    `WebSearchSkill` orchestrates a web search tool (defaults to `TavilySearchTool`)
    to retrieve relevant documents and produces a summary suitable for downstream
    reasoning agents.

    Args:
        search_tool (`Tool`, *optional*):
            An optional search tool instance to use. Defaults to `TavilySearchTool`.
    """

    def __init__(self, search_tool: Optional[Tool] = None):
        self._search_tool = search_tool or TavilySearchTool()

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Researches a topic on the web and returns a synthesized summary of findings."

    async def execute(self, **kwargs: Any) -> Any:
        r"""
        Performs a web search and returns context.

        Args:
            query (`str`):
                The search query to execute.
            **kwargs:
                Additional parameters passed to the search tool.

        Returns:
            `Any`: The search result (typically a string or dictionary of results).

        Example:
            ```python
            >>> skill = WebSearchSkill()
            >>> result = await skill.execute(query="latest AI news")
            ```
        """
        query = kwargs.get("query", "")
        # Standard workflow: Search -> Parse -> Return
        # In a more advanced version, this would include query expansion/refinement.
        raw_results = await self._search_tool.run(query=query, **kwargs)

        # Reference implementation: return the 'answer' or the raw results
        if isinstance(raw_results, dict):
            return raw_results.get("answer", raw_results.get("results", raw_results))

        return raw_results


__all__ = ["WebSearchSkill"]
