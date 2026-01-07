# Agent & Tool Registry

This document tracks the "Lego pieces" available in the `xrtm-forecast` library. We distinguish between the bricks used to build agents and the pre-built specialist roles.

## Core Structural Bricks (`src/forecast/agents/`)

These are the fundamental building blocks used to construct any agentic workflow.

### 1. `LLMAgent` ([llm.py](file:///workspace/forecast/src/forecast/agents/llm.py))
The bridge between an LLM and the forecasting engine.
- **Responsibility**: Prompt management, output parsing, and context maintenance.
- **Usage**: Inherit from this to create your own specialists.

### 2. `ToolAgent` ([tool.py](file:///workspace/forecast/src/forecast/agents/tool.py))
Treats any deterministic Python function as a first-class Agent.
- **Responsibility**: Data transformation, mathematical calculations, or search execution.
- **Usage**: Automatically used when you register a function in the registry.

### 3. `GraphAgent` ([graph.py](file:///workspace/forecast/src/forecast/agents/graph.py))
A composite brick that treats an entire sub-graph as a single agent.
- **Responsibility**: Hierarchical reasoning or nested task parallelization.

---

## Specialist Roles (`src/forecast/agents/specialists/`)

Pre-assembled kits designed for specific analytical missions.

### 1. `ForecastingAnalyst` ([analyst.py](file:///workspace/forecast/src/forecast/agents/specialists/analyst.py))
Our flagship analyst implementation.
- **Role**: Bayesian-style probability estimation.
- **Key Output**: High-fidelity logical traces and confidence scores.

---

## Tool Registry (`src/forecast/tools/`)

The `tool_registry` centralizes external capabilities available to all agents.

### Standard Tools
- **`FunctionTool`**: Automatically wraps standard Python functions.
- **Strand-Agents Integration**: Use `tool_registry.register_strand_tool(tool)` to ingest third-party SDK tools.

---

## Usage Guide: How to Find What You Need

1.  **If you want to build a new agent from scratch**: Start with `LLMAgent`.
2.  **If you want to use the built-in forecasting logic**: Use `ForecastingAnalyst`.
3.  **If you want to add a capability (like a Search engine)**: Register it in the `tool_registry`.
4.  **If you want to discover what's available globally**: Use the `registry` (Agent Registry) or `tool_registry`.
