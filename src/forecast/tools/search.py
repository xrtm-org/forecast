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
from typing import Any, Dict, Optional

import aiohttp

from forecast.tools.base import Tool

logger = logging.getLogger(__name__)


class TavilySearchTool(Tool):
    r"""
    A Tool for performing web searches via the Tavily API.

    Tavily is optimized for LLM consumption, providing concise and relevant
    search results or direct answers to queries.

    Args:
        api_key (`str`, *optional*):
            The Tavily API key. If not provided, it will be read from the
            `TAVILY_API_KEY` environment variable.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            logger.warning("Tavily API key not found. TavilySearchTool will fail if called.")

    @property
    def name(self) -> str:
        return "tavily_search"

    @property
    def description(self) -> str:
        return "Search the web for real-time information and news."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query to execute."},
                "search_depth": {
                    "type": "string",
                    "description": "The depth of the search (basic or advanced).",
                    "default": "basic",
                },
            },
            "required": ["query"],
        }

    async def run(self, **kwargs: Any) -> Any:
        r"""
        Executes a search query against the Tavily API.

        Args:
            query (`str`):
                The search query.
            search_depth (`str`, *optional*, defaults to `"basic"`):
                The depth of the search.

        Returns:
            `Any`: The JSON response from the Tavily API, or an error message.
        """
        query = kwargs.get("query")
        search_depth = kwargs.get("search_depth", "basic")
        if not self.api_key:
            return "Error: TAVILY_API_KEY missing. Cannot perform search."

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "include_answer": True,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return f"Error from Tavily API: {error_text}"

                    data = await response.json()
                    return data
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return f"Error executed search: {str(e)}"


__all__ = ["TavilySearchTool"]
