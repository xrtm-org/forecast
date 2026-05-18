# Customizing Agents & Execution Graphs

`xrtm-forecast` is designed as a composable runtime. Extend the runtime by adding agents, tools, and execution-graph nodes.

## 1. Creating a custom agent

To build a custom agent, inherit from `forecast.Agent` and implement `run`.

```python
from xrtm.forecast import Agent

class SentimentAgent(Agent):
    def __init__(self, name="Sentiment"):
        super().__init__(name)

    async def run(self, text: str, **kwargs):
        return {"sentiment": "bullish", "score": 0.8}
```

## 2. Designing a custom execution graph

The `Orchestrator` manages an execution graph: registered nodes plus transition logic.

### Step 1: define nodes
Every node must accept `state` (`BaseGraphState`) and `on_progress` (`Callable`).

```python
async def research_node(state, on_progress):
    result = await my_agent.run(state.subject_id)
    state.context["research"] = result
    return "analysis"
```

### Step 2: assemble with the orchestrator

```python
from xrtm.forecast import Orchestrator

orchestrator = Orchestrator()
orchestrator.register_node("research", research_node)
orchestrator.register_node("analysis", analysis_node)

final_state = await orchestrator.run(state, entry_node="research")
```

## 3. Real-world example

See [custom_sentiment_workflow.py](examples/kit/pipelines/custom_sentiment_workflow/run_custom_sentiment_workflow.py) for a runnable example that keeps the legacy directory name but demonstrates:

- custom Pydantic result schemas,
- conditional branching between stages,
- multi-agent orchestration inside one execution graph.
