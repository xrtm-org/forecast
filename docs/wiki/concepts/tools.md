# Tools & Skills

In `xrtm-forecast`, we distinguish between **Tools** (low-level actions) and **Skills** (high-level capabilities).

## 1. Tools (The "Scalpel")
A **Tool** is a single, deterministic Python function. It is intended for granular tasks.

```python
@tool
def get_stock_price(ticker: str):
    """Fetches the latest EOD price."""
    return 150.0
```

## 2. Skills (The "Ability")
A **Skill** is a high-level **bundle**. It represents an agent's "professional training" in a specific domain. Skills often contain multiple tools and specific safety/logic checks.

| Skill | Description |
| :--- | :--- |
| **SQLSkill** | The ability to safely query and analyze relational data. |
| **SearchSkill** | The ability to research and cite external sources. |
| **VizSkill** | The ability to generate reliability diagrams and charts. |
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
