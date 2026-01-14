# Orchestration Engine

The `Orchestrator` is the domain-agnostic engine that drives all agent workflows in `xrtm-forecast`. It implements a state machine that transitions a `BaseGraphState` through a set of Nodes.

## Key Concepts

### Stages (The "Functional Slots")
A Stage (implemented as a `Node` in code) is a unit of execution—a "slot" in your workflow.
*   **Agent Stages**: Powered by an LLM (e.g., "The Forecaster").
*   **Utility Stages**: Pure Python functions (e.g., "The Math Model" or "The Data Fetcher").

This distinction is what enables the Quant-Agent Hybrid: you can have a high-speed statistical model as one Stage and a creative reasoning agent as another in the same graph.

```python
# A Node can be a simple function
def calculate_brier_score(state: BaseGraphState, progress):
    # Pure math, no LLM needed
    return "end"

orch.add_node("math_step", calculate_brier_score)
```

### Edges
An Edge defines the control flow.
```python
# Declarative wiring
orch.add_edge("node_a", "node_b")
```

### Parallel Groups (v0.1.5+)
A Parallel Group allows multiple Stages to execute concurrently. The Orchestrator waits for *all* stages in the group to complete (Barrier Synchronization) before moving to the next step.

This is essential for high-throughput workflows where components don't depend on each other's immediate output.

**Example:**
```python
# 1. Register Nodes
orch.add_node("worker_1", w1)
orch.add_node("worker_2", w2)

# 2. Define Parallel Group
orch.add_parallel_group("run_all", ["worker_1", "worker_2"])

# 3. Wire
orch.add_edge("start", "run_all")
orch.add_edge("run_all", "aggregator")
```

## Execution Loop (v0.3.0 Standard)

For "Institutional Grade" performance and safety, never run the Orchestrator with raw `asyncio.run()`. Always use the `AsyncRuntime`.

```python
from forecast import AsyncRuntime, Orchestrator

async def main():
    orch = Orchestrator(...)
    # Setup graph...
    result = await orch.run(input_data)
    print(result)

if __name__ == "__main__":
    AsyncRuntime.run_main(main())
```

## Control Flow
1.  **Entry Point**: The graph starts at `entry_point`.
2.  **Execution**: The active Stage runs.
3.  **Transition**:
    *   If the stage code returns a `next_stage` string, execution jumps there.
    *   If it returns `None`, the Orchestrator checks the `edges` registry.
    *   If no edge matches, execution stops.
4.  **Cycles**: A `max_cycles` safeguard prevents infinite loops.
