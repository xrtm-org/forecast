# Orchestrator Basics

**Script**: `run_orchestrator_basics.py`

This example demonstrates the fundamental building blocks of the `xrtm-forecast` reasoning engine: the Graph, Nodes, and Edges. It shows how to construct a simple Directed Acyclic Graph (DAG) for orchestrated execution.

## Usage

```bash
# From repository root
python3 examples/core/orchestrator_basics/run_orchestrator_basics.py
```

## What it does
1.  **Registers Nodes**: Defines simple Python functions as runnable graph nodes.
2.  **Defines Topology**: Connects nodes with dependencies (Edges).
3.  **Executes Graph**: Runs the graph and prints the execution order.
