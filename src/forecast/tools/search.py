import logging
import os
from typing import Any, Dict, Optional

import aiohttp

from forecast.tools.base import Tool

logger = logging.getLogger(__name__)

class TavilySearchTool(Tool):
    """
    Tool for searching the web using the Tavily API.
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
                "query": {
                    "type": "string",
                    "description": "The search query to execute."
                },
                "search_depth": {
                    "type": "string",
                    "description": "The depth of the search (basic or advanced).",
                    "default": "basic"
                }
            },
            "required": ["query"]
        }

    async def run(self, **kwargs: Any) -> Any:
        query = kwargs.get("query")
        search_depth = kwargs.get("search_depth", "basic")
        if not self.api_key:
            return "Error: TAVILY_API_KEY missing. Cannot perform search."

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "include_answer": True
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
