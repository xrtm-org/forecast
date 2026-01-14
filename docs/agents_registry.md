# Agent & Tool Registry

This document tracks the "Lego pieces" available in the `xrtm-forecast` library. We distinguish between the bricks used to build agents and the pre-built specialist roles.

## Core Structural Bricks (`src/forecast/kit/agents/`)

These are the fundamental building blocks used to construct any agentic workflow.

### 1. `LLMAgent` ([llm.py](file:///workspace/forecast/src/forecast/kit/agents/llm.py))
The bridge between an LLM and the forecasting engine.
- **Responsibility**: Prompt management, output parsing, and context maintenance.
- **Usage**: Inherit from this to create your own specialists.

### 2. `ToolAgent` ([tool.py](file:///workspace/forecast/src/forecast/kit/agents/tool.py))
Treats any deterministic Python function as a first-class Agent.
- **Responsibility**: Data transformation, mathematical calculations, or search execution.
- **Usage**: Automatically used when you register a function in the registry.

### 3. `GraphAgent` ([graph.py](file:///workspace/forecast/src/forecast/kit/agents/graph.py))
A composite brick that treats an entire sub-graph as a single agent.
- **Responsibility**: Hierarchical reasoning or nested task parallelization.

---

## Specialist Roles (`src/forecast/kit/agents/`)

Pre-assembled kits designed for specific analytical missions.

### 1. `ForecastingAnalyst` ([analyst.py](file:///workspace/forecast/src/forecast/kit/agents/specialists/analyst.py))
Our flagship analyst implementation using Bayesian-style probability estimation.

### 2. `FactCheckerAgent` ([fact_checker.py](file:///workspace/forecast/src/forecast/kit/agents/fact_checker.py))
Dedicated specialist for Natural Language Inference (NLI) based claim verification.

### 3. `AdversaryAgent` ([adversary.py](file:///workspace/forecast/src/forecast/kit/agents/specialists/adversary.py))
Red-teaming specialist that identifies logical fallacies and biases in reasoning.

---

## Skill & Tool Registries

### 1. Skill Registry (`src/forecast/kit/skills/`)
The high-level behaviors available to agents.
*   **Usage**: `agent.add_skill(MarketResearchSkill())`.
*   **Contains**: Complex workflows (Search + RAG + Summarization).

### 2. Tool Registry (`src/forecast/providers/tools/`)
The low-level driver functions.
*   **Usage**: Used by Skills, rarely by Agents directly.
*   **Contains**: Atomic drivers (`GoogleSearchTool`, `CalculatorTool`).
*   **Strand-Agents Integration**: Use `tool_registry.register_strand_tool(tool)` to ingest third-party SDK tools.

---

## Usage Guide: How to Find What You Need

1.  **If you want to build a new agent from scratch**: Start with `LLMAgent`.
2.  **If you want to use the built-in forecasting logic**: Use `ForecastingAnalyst`.
3.  **If you want to add a skill (like a Search engine)**: Register it in the `skill_registry`.
4.  **If you want to discover what's available globally**: Use the `registry` (Agents), `skill_registry` (high-level), or `tool_registry` (low-level).
