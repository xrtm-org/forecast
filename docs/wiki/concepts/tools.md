# Tools

A **Tool** (or Skill) is a deterministic function that an Agent can execute. Tools bridge the gap between the LLM's reasoning and the real world.

## Standard Library
`xrtm-forecast` includes "Institutional Grade" tools:

| Tool | Purpose |
| :--- | :--- |
| `SQLSkill` | Safe, read-only database querying. |
| `PandasSkill` | Dataframe manipulation (filtering, aggregation). |
| `SearchSkill` | Web search for external data. |

## Creating Custom Tools
Use the `@tool` decorator to turn any Python function into a skill.

```python
from forecast.tools import tool

@tool("calculate_var")
def calculate_risk(portfolio_value: float, confidence: float = 0.95) -> float:
    """Calculates Value at Risk (VaR)."""
    # ... logic ...
    return 1000.0
```

## Security Note
Tools run with the full permissions of the host process. Always review custom tools for security vulnerabilities (e.g., `subprocess.run`).
