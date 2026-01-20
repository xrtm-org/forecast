# Tools & Skills

In `xrtm-forecast`, we distinguish between Tools (low-level actions) and Skills (high-level capabilities).

## 1. Tools (The "Scalpel")
A Tool is a single, deterministic Python function. It is intended for granular tasks.

```python
from forecast.providers.tools import FunctionTool

def get_atmospheric_pressure(station_id: str):
    """Fetches the latest EOD pressure reading."""
    return 1013.25

pressure_tool = FunctionTool(get_atmospheric_pressure)
```

## 2. Skills (The "Ability")
A Skill is a high-level bundle. It represents an agent's "professional training" in a specific domain. Skills often contain multiple tools and specific safety/logic checks.

| Skill | Description |
| :--- | :--- |
| **SQLSkill** | The ability to safely query and analyze relational data. |
| **WebSearchSkill** | The ability to research and cite external sources. |
| **VizSkill** | The ability to generate reliability diagrams and charts. |
Use the `FunctionTool` wrapper or `tool_registry` to turn any Python function into a skill.

```python
from forecast.providers.tools import FunctionTool

def calculate_variance(data_points: list[float]) -> float:
    """Calculates the statistical variance of a dataset."""
    # ... logic ...
    return 25.0

variance_tool = FunctionTool(calculate_variance)
```

## Security Note
Tools run with the full permissions of the host process. Always review custom tools for security vulnerabilities (e.g., `subprocess.run`).
