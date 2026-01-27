# Human-in-the-Loop (Centaur Protocol)

The **Centaur Protocol** enables hybrid human-AI forecasting where AI handles divergent research and humans provide convergent judgment.

## The Problem: The Silicon Ceiling

Pure AI forecasting plateaus at ~70% accuracy on complex geopolitical questions because models lack "tacit knowledge"—the intuitive understanding that comes from lived experience.

Meanwhile, human experts have deep intuition but can't process 10,000 news articles per hour.

> **Research Evidence**: The Good Judgment Project found that "Centaur" teams (humans + AI) consistently outperform both pure AI and pure human forecasters.

## The Solution: Cyborg Forecasting

`xrtm-forecast` implements a protocol where:

1. **AI does the Divergent work** — Finding 50 obscure facts across sources
2. **Human does the Convergent work** — Weighing the facts to make final judgment
3. **AI Calibrates the Human** — Warning about base-rate neglect and cognitive biases

### The Analyst Workbench

A topology where the central node is a human analyst:

```python
from xrtm.forecast.kit.workbench import AnalystWorkbench
from xrtm.forecast.kit.agents import LLMAgent

# Create research agents
researchers = [
    LLMAgent(name="NewsScanner", ...),
    LLMAgent(name="DataAnalyst", ...),
]

# Build the workbench
workbench = AnalystWorkbench(agents=researchers)
orchestrator = workbench.build_orchestrator(
    reviewer_prompt="Review the research and provide your probability estimate"
)

# The orchestrator will pause at the human node and wait for input
```

### The Bias Interceptor

An AI auditor that checks human reasoning for cognitive biases:

```python
from xrtm.eval.kit.eval.bias import BiasInterceptor

interceptor = BiasInterceptor(model=llm)
audit_result = await interceptor.evaluate_reasoning(
    "I'm 95% confident because I just read a vivid news article about this..."
)
# Returns: {
#   "detected_biases": ["Availability Heuristic", "Overconfidence"],
#   "severity": 7,
#   "explanation": "Recency of information may be inflating confidence..."
# }
```

## Implementing Human Nodes

The Orchestrator natively supports `human:` prefixed nodes:

```python
from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.interfaces import HumanProvider

class CLIHumanProvider(HumanProvider):
    async def get_human_input(self, prompt: str) -> str:
        print(f"\n🧠 HUMAN INPUT REQUIRED:\n{prompt}\n")
        return input("Your response: ")

# Add human provider to state context
state.context["human_provider"] = CLIHumanProvider()

# The orchestrator will call get_human_input when it reaches a human: node
orchestrator.add_edge("research_phase", "human:What is your probability estimate?")
```

Human judgments are **Merkle-anchored** just like AI reasoning, ensuring full auditability.

## Trade-offs

| Aspect | Consideration |
| :--- | :--- |
| **Latency** | Human response time (minutes/hours vs milliseconds) |
| **Scalability** | Cannot parallelize human judgment |
| **Use Case** | Best for high-stakes, low-frequency decisions |

## Related Concepts

- [Orchestration](orchestration.md) — How human nodes integrate with the graph engine
- [Merkle Sovereignty](merkle_sovereignty.md) — How human judgments are audit-locked
