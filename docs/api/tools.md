# Tools API

Tools are atomic, stateless capabilities that skills orchestrate.

::: xrtm.forecast.kit.tools.search.TavilySearchTool
    options:
      show_root_heading: true

> **Changed in 0.9–0.10.** The bundled `WaybackTool` was removed. For web
> research, pair `WebSearchSkill` with a tool implementing `search()` /
> `search_formatted()` (Tavily, or a free DuckDuckGo adapter in your application).

See [Skills](skills.md) for the skill layer.
