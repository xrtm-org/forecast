# Agent & Tool Registry

This document tracks the reusable building blocks available in `xrtm-forecast`.

## Core structural bricks (`src/xrtm/forecast/kit/agents/`)

These are the fundamental building blocks used to construct execution graphs and forecast runs.

### 1. `LLMAgent` ([llm.py](../src/xrtm/forecast/kit/agents/llm.py))
The bridge between an LLM and the forecasting runtime.
- **Responsibility**: prompt management, output parsing, and context maintenance.
- **Usage**: inherit from this to create specialists.

### 2. `ToolAgent` ([tool.py](../src/xrtm/forecast/kit/agents/tool.py))
Treats deterministic Python functions as first-class agents.
- **Responsibility**: data transformation, mathematical calculations, or search execution.
- **Usage**: use when a stage should run deterministic code inside the execution graph.

### 3. `GraphAgent` ([graph.py](../src/xrtm/forecast/kit/agents/graph.py))
A composite brick that treats an entire execution graph as a single agent.
- **Responsibility**: hierarchical reasoning or nested task parallelization.

## Specialist roles (`src/xrtm/forecast/kit/agents/specialists/`)

### 1. `ForecastingAnalyst` ([analyst.py](../src/xrtm/forecast/kit/agents/specialists/analyst.py))
Flagship analyst implementation using Bayesian-style probability estimation.
Supports `prompt_template`, `structured_output`, `strict_parse`, and `strict_dag`.

> **Changed in 0.9–0.10.** The `FactCheckerAgent` and `AdversaryAgent`
> specialists were removed; verification-style work is expressed with decision
> providers and the escalation router (below).

## Decision roles (`src/xrtm/forecast/kit/decisions/`)

### 1. `EscalationRouter` ([escalation.py](../src/xrtm/forecast/kit/decisions/escalation.py))
Routes typed decisions between a cheap System-One provider (e.g. Jev) and a
stronger LLM fallback when confidence is low.

### 2. Decision providers ([decision.py](../src/xrtm/forecast/providers/inference/decision.py))
`LLMDecisionProvider` (any JSON-capable provider) and `JevProvider`.

## Skill & tool registries

### Skill registry (`src/xrtm/forecast/kit/skills/`)
High-level behaviors available to agents.
- **Usage**: `agent.add_skill(WebSearchSkill())`
- **Contains**: `WebSearchSkill` (Tavily, or any tool implementing `search()` / `search_formatted()`).

### Tool registry (`src/xrtm/forecast/core/tools/registry.py`, implementations in `kit/tools/`)
Low-level driver functions.
- **Usage**: used by skills, rarely by agents directly.
- **Contains**: `TavilySearchTool`; wrap plain functions with `FunctionTool`.
- **Strand-Agents Integration**: use `tool_registry.register_strand_tool(tool)` to ingest third-party SDK tools.
