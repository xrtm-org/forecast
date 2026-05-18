# Orchestrator Basics

**Script**: `run_orchestrator_basics.py`

This example demonstrates the fundamental building blocks of the `xrtm-forecast` runtime: the execution graph, nodes, and edges.

## Usage

```bash
python3 examples/core/orchestrator_basics/run_orchestrator_basics.py
```

## What it does

1. **Registers nodes**: defines simple Python functions as runnable execution-graph nodes.
2. **Defines control flow**: connects nodes with edges.
3. **Runs a forecast path**: executes the graph and prints the execution trace.
