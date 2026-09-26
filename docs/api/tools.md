# Tools API

Tools are atomic, stateless capabilities that skills orchestrate.

::: xrtm.forecast.kit.tools.search.TavilySearchTool
    options:
      show_root_heading: true

> **Changed in 0.9–0.10.** The bundled `WaybackTool` was removed. For web
> research, pair `WebSearchSkill` with a tool implementing `search()` /
> `search_formatted()` (Tavily, or a free DuckDuckGo adapter in your application).

See [Skills](skills.md) for the skill layer.

## Caching tool calls

Wrap any search tool with `CachedSearchTool` to cut API calls and make
backtests reproducible (same query → same evidence, TTL-controlled):

```python
from xrtm.forecast.kit.tools import CachedSearchTool

cached = CachedSearchTool(my_search_tool, ttl_seconds=86_400)
results = cached.search("inflation expectations", max_results=5)
print(cached.stats)  # hits/misses + underlying cache stats
```
