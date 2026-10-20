# Tools API

Tools are atomic, stateless capabilities that skills orchestrate.

::: xrtm.forecast.kit.tools.search.TavilySearchTool
    options:
      show_root_heading: true

::: xrtm.forecast.kit.tools.search.DeepSeekSearchTool
    options:
      show_root_heading: true

> **Changed in 0.9–0.10.** The bundled `WaybackTool` was removed. For web
> research, pair `WebSearchSkill` with a tool implementing `search()` /
> `search_formatted()` (Tavily, DeepSeek's in-house Search API, or a free
> DuckDuckGo adapter in your application).

> **DeepSeek search (0.13.6).** `DeepSeekSearchTool` calls
> `POST /v1/tools/search` and costs ¥5 per 1,000 **successful** requests
> (billed only for non-empty results; free until 2026-11-01). It uses the same
> `DEEPSEEK_API_KEY` as chat, and `WebSearchSkill()` selects it automatically
> when no Tavily key is set. Reasoning-capable models can set
> `OpenAIConfig.reasoning_effort="low"` to control output-token cost.

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

## Lexical retrieval

`LexicalRetriever` indexes strings or dict documents with BM25 (zero
dependencies) for archive search and dedup — no embedding model required:

```python
from xrtm.forecast.kit.skills.retrieval import LexicalRetriever

retriever = LexicalRetriever(news_items, text_key="title")
top = retriever.search("fed rate cut", k=5)
```
