# Orchestration Engine

The `Orchestrator` is the domain-agnostic engine that drives all agent workflows in `xrtm-forecast`. It implements a state machine that transitions a `BaseGraphState` through a set of Nodes.

## Key Concepts

### Nodes
A **Node** is a unit of execution (function or wrapped Agent).
```python
orch.add_node("node_a", my_function)
```

### Edges
An **Edge** defines the control flow.
```python
# Declarative wiring
orch.add_edge("node_a", "node_b")
```

### Parallel Groups (New in v0.1.5)
A **Parallel Group** allows multiple nodes to execute **concurrently**. The Orchestrator waits for *all* nodes in the group to complete (Barrier Synchronization) before moving to the next step.

This is essential for high-throughput workflows where agents don't depend on each other's immediate output.

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

## Control Flow
1.  **Entry Point**: The graph starts at `entry_point` (default: "ingestion").
2.  **Execution**: The active node runs.
3.  **Transition**:
    *   If the node returns a `next_node` string, execution jumps there.
    *   If the node returns `None`, the Orchestrator checks the `edges` registry.
    *   If no edge matches, execution stops.
4.  **Cycles**: A `max_cycles` safeguard prevents infinite loops.
