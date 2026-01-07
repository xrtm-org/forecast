from typing import Any, Optional

from forecast.skills.definitions import BaseSkill
from forecast.tools.base import Tool
from forecast.tools.search import TavilySearchTool


class WebSearchSkill(BaseSkill):
    """
    Skill for gathering information from the web.
    Orchestrates a search tool and provides a synthesized context.
    """
    def __init__(self, search_tool: Optional[Tool] = None):
        # Default to Tavily if no tool provided
        self._search_tool = search_tool or TavilySearchTool()

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Researches a topic on the web and returns a synthesized summary of findings."

    async def execute(self, **kwargs: Any) -> Any:
        query = kwargs.get("query", "")
        # Standard workflow: Search -> Parse -> Return
        # In a more advanced version, this would include query expansion/refinement.
        raw_results = await self._search_tool.run(query=query, **kwargs)

        # Reference implementation: return the 'answer' or the raw results
        if isinstance(raw_results, dict):
            return raw_results.get("answer", raw_results.get("results", raw_results))

        return raw_results
