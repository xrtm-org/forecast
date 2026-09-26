# Human-in-the-Loop (Centaur Protocol)

The **Centaur Protocol** enables hybrid human-AI forecasting where AI handles
divergent research and humans provide convergent judgment.

## The Problem: The Silicon Ceiling

Pure AI forecasting plateaus on complex geopolitical questions because models
lack "tacit knowledge"—the intuitive understanding that comes from lived
experience. Meanwhile, human experts have deep intuition but cannot process
10,000 news articles per hour.

> **Research Evidence**: The Good Judgment Project found that "Centaur" teams
> (humans + AI) consistently outperform both pure AI and pure human forecasters.

## The Solution: Cyborg Forecasting

`xrtm-forecast` implements a protocol where:

1. **AI does the Divergent work** — finding obscure facts across sources
2. **Human does the Convergent work** — weighing the facts to make final judgment
3. **AI Calibrates the Human** — surfacing base rates and structured context

> **Changed in 0.9–0.10.** The `AnalystWorkbench` helper and the
> `BiasInterceptor` auditor were removed. Human input is supported through
> `HumanProvider` + `human:` orchestration nodes (below).

## Implementing Human Nodes

The Orchestrator natively supports `human:` prefixed nodes:

```python
from xrtm.forecast.core.interfaces import HumanProvider
from xrtm.forecast.core.orchestrator import Orchestrator


class CLIHumanProvider(HumanProvider):
    async def get_human_input(self, prompt: str) -> str:
        print(f"\nHUMAN INPUT REQUIRED:\n{prompt}\n")
        return input("Your response: ")


# Add the human provider to state context
state.context["human_provider"] = CLIHumanProvider()

# The orchestrator calls get_human_input when it reaches a human: node
orchestrator.add_edge("research_phase", "human:What is your probability estimate?")
```

Human judgments flow through the same execution trace as AI reasoning,
preserving auditability.

## Trade-offs

| Aspect | Consideration |
| :--- | :--- |
| **Latency** | Human response time (minutes/hours vs milliseconds) |
| **Scalability** | Cannot parallelize human judgment |
| **Use Case** | Best for high-stakes, low-frequency decisions |

## Related Concepts

- [Orchestration](orchestration.md) — How human nodes integrate with the graph engine
- [Merkle Sovereignty](merkle_sovereignty.md) — How judgments are audit-locked
