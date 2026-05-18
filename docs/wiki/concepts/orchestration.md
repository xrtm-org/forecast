# Orchestration Engine

The `Orchestrator` is the domain-agnostic engine that drives execution graphs in `xrtm-forecast`. It moves a `BaseGraphState` through registered nodes and records the execution trace for each run.

## Key concepts

### Nodes and stages

A **node** is the engine's registered execution unit. A **stage** is the role that node plays in a topology or pipeline.

- **Agent stages**: powered by an LLM or other reasoning component.
- **Utility stages**: pure Python functions or deterministic tools.

This distinction lets you mix fast statistical models with slower deliberative agents in the same execution graph.

```python
# A node can be a simple function.
def calculate_brier_score(state: BaseGraphState, progress):
    return "end"

orch.add_node("math_step", calculate_brier_score)
```

### Edges
An edge defines execution-graph control flow.

```python
orch.add_edge("node_a", "node_b")
```

### Parallel groups
A parallel group allows multiple nodes to execute concurrently. The orchestrator waits for all nodes in the group before the run continues.

```python
orch.add_node("worker_1", w1)
orch.add_node("worker_2", w2)
orch.add_parallel_group("run_all", ["worker_1", "worker_2"])
orch.add_edge("start", "run_all")
orch.add_edge("run_all", "aggregator")
```

## Execution loop

Use `AsyncRuntime` rather than raw `asyncio.run()` when starting production code.

```python
from xrtm.forecast import AsyncRuntime, Orchestrator

async def main():
    orch = Orchestrator(...)
    result = await orch.run(input_data)
    print(result)

if __name__ == "__main__":
    AsyncRuntime.run_main(main())
```

## Control flow

1. **Entry point**: the execution graph starts at `entry_point`.
2. **Execution**: the active node runs.
3. **Transition**:
   - If stage code returns a `next_stage` string, execution jumps there.
   - If it returns `None`, the orchestrator checks the edge registry.
   - If no edge matches, execution stops.
4. **Cycles**: a `max_cycles` safeguard prevents infinite loops.
