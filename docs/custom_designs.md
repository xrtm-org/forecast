# Customizing Agents & Graphs

The `xrtm-forecast` library is designed as a "Lego-piece" architecture. Here is how you can extend it.

## 1. Creating a Custom Agent

To build a custom agent, inherit from `forecast.Agent` and implement the `run` method.

```python
from forecast import Agent

class SentimentAgent(Agent):
    def __init__(self, name="Sentiment"):
        super().__init__(name)

    async def run(self, text: str, **kwargs):
        # Your custom logic here
        return {"sentiment": "bullish", "score": 0.8}
```

## 2. Designing a Custom Graph

Graphs are managed by the `Orchestrator`. A graph is a set of "Nodes" (can be agents or functions) and a "Transition Logic".

### Step 1: Define your Nodes
Every node must accept `state` (BaseGraphState) and `on_progress` (Callable).

```python
async def research_node(state, on_progress):
    # Call an agent
    result = await my_agent.run(state.subject_id)
    state.context["research"] = result
    return "analysis" # Name of the target node
```

### Step 2: Assemble with the Orchestrator

```python
from forecast import Orchestrator

orchestrator = Orchestrator()
orchestrator.register_node("research", research_node)
orchestrator.register_node("analysis", analysis_node)

# Run the graph
final_state = await orchestrator.run(state, entry_node="research")
```

## 4. Real-World Example
See [custom_sentiment_workflow.py](examples/kit/pipelines/custom_sentiment_workflow.py) for a complete, runnable example featuring:
- Custom Pydantic result schemas.
- Conditional branching (Sentiment -> Trend check).
- Multi-agent orchestration.
