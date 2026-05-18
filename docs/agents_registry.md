# Agent & Tool Registry

This document tracks the reusable building blocks available in `xrtm-forecast`.

## Core structural bricks (`src/xrtm/forecast/kit/agents/`)

These are the fundamental building blocks used to construct execution graphs and forecast runs.

### 1. `LLMAgent` ([llm.py](../src/xrtm/forecast/kit/agents/llm.py))
The bridge between an LLM and the forecasting runtime.
- **Responsibility**: prompt management, output parsing, and context maintenance.
- **Usage**: inherit from this to create specialists.

### 2. `ToolAgent` ([tool.py](../src/xrtm/forecast/kit/agents/tool.py))
Treats any deterministic Python function as a first-class agent.
- **Responsibility**: data transformation, mathematical calculations, or search execution.
- **Usage**: use when a stage should run deterministic code inside the execution graph.

### 3. `GraphAgent` ([graph.py](../src/xrtm/forecast/kit/agents/graph.py))
A composite brick that treats an entire execution graph as a single agent.
- **Responsibility**: hierarchical reasoning or nested task parallelization.

## Specialist roles (`src/xrtm/forecast/kit/agents/`)

Pre-assembled agents designed for specific analytical missions.

### 1. `ForecastingAnalyst` ([analyst.py](../src/xrtm/forecast/kit/agents/specialists/analyst.py))
Flagship analyst implementation using Bayesian-style probability estimation.

### 2. `FactCheckerAgent` ([fact_checker.py](../src/xrtm/forecast/kit/agents/fact_checker.py))
Dedicated specialist for Natural Language Inference (NLI)-based claim verification.

### 3. `AdversaryAgent` ([adversary.py](../src/xrtm/forecast/kit/agents/specialists/adversary.py))
Red-teaming specialist that identifies logical fallacies and biases in reasoning.

## Skill & tool registries

### Skill registry (`src/xrtm/forecast/kit/skills/`)
High-level behaviors available to agents.
- **Usage**: `agent.add_skill(MarketResearchSkill())`
- **Contains**: assembled run patterns such as search + retrieval + summarization.

### Tool registry (`src/xrtm/forecast/providers/tools/`)
Low-level driver functions.
- **Usage**: used by skills, rarely by agents directly.
- **Contains**: atomic drivers (`GoogleSearchTool`, `CalculatorTool`).
- **Strand-Agents Integration**: use `tool_registry.register_strand_tool(tool)` to ingest third-party SDK tools.
