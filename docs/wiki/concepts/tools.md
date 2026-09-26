# Tools & Skills

In `xrtm-forecast`, we distinguish between Tools (low-level actions) and Skills
(high-level capabilities).

## 1. Tools (The "Scalpel")

A Tool is a single, deterministic Python function wrapped for graph use.

```python
from xrtm.forecast.core.tools.base import FunctionTool


def get_atmospheric_pressure(station_id: str) -> float:
    """Fetches the latest pressure reading."""
    return 1013.25


pressure_tool = FunctionTool(get_atmospheric_pressure)
```

## 2. Skills (The "Ability")

A Skill is a high-level bundle: an agent's "professional training" in a domain.
Skills often orchestrate multiple tools plus safety/logic checks.

| Skill | Description |
| :--- | :--- |
| **WebSearchSkill** | Research and cite external sources (Tavily, or any tool implementing `search()` / `search_formatted()`). |

Attach skills with `agent.add_skill(...)`; the `ForecastingAnalyst` uses the
`web_search` skill automatically when present. Additional skills implement
`BaseSkill` from `xrtm.forecast.kit.skills.definitions`.

## Security Note

Tools run with the full permissions of the host process. Always review custom
tools for security vulnerabilities (e.g. `subprocess.run`).
