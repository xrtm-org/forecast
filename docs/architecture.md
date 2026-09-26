# Architecture & Design Principles

`xrtm-forecast` is built on a "Platform vs. Application" architecture. We distinguish clearly between the **Engine** (the execution-graph bricks) and the **Experts** (the pre-assembled kits).

## Ecosystem Overview

`xrtm-forecast` is part of a four-package ecosystem with strict layer dependencies:

| Layer | Package | Role | Can Import From |
|-------|---------|------|-----------------|
| 4 | `xrtm-train` | Backtesting, calibration | forecast, eval, data |
| 3 | `xrtm-forecast` | Execution-graph engine, agents | eval, data |
| 2 | `xrtm-eval` | Metrics, trust primitives | data |
| 1 | `xrtm-data` | Schemas, snapshots | *(none)* |

> See [.agent/rules/governance.md](../.agent/rules/governance.md) for detailed import rules.

## Terminology

- **Workflow** belongs to the released top-level `xrtm` product story.
- **Run** is one concrete execution of the forecast runtime.
- **Execution graph** is the orchestrator DAG of nodes and edges.
- **Reasoning graph** is the causal structure captured inside a forecast result.
- **Topology** is a reusable execution-graph pattern.
- **Pipeline** is a pre-assembled helper that builds a forecast path from stages or topologies.
- **Node** is the engine term; **stage** is the role that node plays in docs and examples.

---

## Core Philosophy: The Lego Analogy

To understand how to build with this library, imagine a Lego set:

1.  Abstractions (The Bricks): These are the fundamental shapes. A 2x4 brick doesn't know if it's part of a car or a house; it only knows how to click into other bricks.
2.  Specialists (The Kits): These are pre-designed models (like a Lego Starship). They come with instructions and a specific "mindset," but they are built entirely using the standard bricks.
3.  The Registry (The Catalog): This is where you find which bricks and kits are currently available to use.

---

## The Agent Hierarchy

We organize the `agents/` directory to reflect this split. This ensures the engine remains "lean" while the library of experts can grow infinitely.

### 1. Structural Abstractions (`src/xrtm/forecast/kit/agents/*.py`)
These are the Shapes. They define mechanical behavior, not business logic.
- **`Agent`**: The base contract. Defines how an object interacts with an execution graph.
- **`LLMAgent`**: The bridge to intelligence. Knows how to prompt, parse, and handle model context.
- **`ToolAgent`**: The wrapper for deterministic code. Allows standard functions to live in the execution graph.
- **`GraphAgent`**: The recursion brick. Allows an entire execution graph (often assembled by a pipeline helper) to be treated as a single agent.

### 2. Specialist Implementations (`src/xrtm/forecast/kit/agents/specialists/*.py`)
These are the Roles. They are built by inheriting from the abstractions above.
- **`ForecastingAnalyst`**: A pre-built persona that uses Bayesian reasoning to solve problems.
- **Verification & routing**: `DecisionProvider` + `EscalationRouter` handle claim checks and cheap-vs-strong routing (`kit/decisions/`).
- **`RecursiveConsensus`**: A topology for peer review and loop-back (`kit/topologies/consensus.py`).
- **`Generic Agent + Skills`**: We prefer equipping standard agents with skills over creating rigid subclasses.

---

## System Layers

### 1. The Orchestration Layer (`src/xrtm/forecast/core/`)
The `Orchestrator` is the state machine. It doesn't "think"—it just moves the `BaseGraphState` from one execution-graph node to the next based on your configuration.

### 2. The Inference Layer (`src/xrtm/forecast/providers/inference/`)
Standardizes LLM communication. Whether you use Gemini, OpenAI, or a local model, the agent only sees the `InferenceProvider` interface.

### 2a. The Async Runtime (`src/xrtm/forecast/core/runtime.py`)
To ensure "Institutional Grade" safety and performance, we do not use raw `asyncio`.
- **`AsyncRuntime` Facade**: Wraps `legacy` asyncio.
- **Orphan Prevention**: Enforces named tasks for telemetry.
- **Time Travel**: Prepares the system for Chronos by wrapping `sleep()` calls.
- **High Performance**: Automatically installs `uvloop` if available.

### 3. The Skill Layer (`src/xrtm/forecast/kit/skills/`)
Contains the **Skill Registry**.

### Taxonomy: Skills vs. Tools
To keep the system modular, we strictly distinguish between:
*   The Tool (`src/xrtm/forecast/core/tools/`, implementations in `kit/tools/`): An atomic, stateless function (e.g. `TavilySearchTool.execute()`). It wraps a specific driver or API.
*   The Skill (`src/xrtm/forecast/kit/skills/`): A high-level behavior that *uses* tools (e.g. `WebSearchSkill`). It manages retries, error handling, and prompt logic.

*Rule: Agents possess Skills. Skills control Tools.*

### 4. Protocols & Physics
- **Chronos (Time)**: `TemporalContext` acts as the single source of truth for time. The `GuardianTool` wrapper enforces this by blocking non-PiT tools during backtests.
- **Sentinel (Space)**: `ForecastTrajectory` captures the *evolution* of a probability over time, not just the final snapshot.
- **Equilibrium (Calibration)**: Scoring and calibration live in **xrtm-eval** (`BrierScoreEvaluator`, `ExpectedCalibrationErrorEvaluator`), which audit whether subjective confidence matches objective frequencies.

## Data Flow & Traceability

We use a double-trace methodology for every forecast:

```mermaid
graph TD
    A[Input Question] --> B[Orchestrator]
    B --> C{Execution Graph Nodes}
    C -- "Agent 1" --> D[Execution Trace]
    C -- "Agent 2" --> D
    D --> E[Audit Log]
    C -- "Reasoning" --> F[Reasoning Trace]
    F --> G[Final Forecast]
```

> Scoring/calibration evaluators (`BrierScoreEvaluator`,
> `ExpectedCalibrationErrorEvaluator`) live in **xrtm-eval**; backtesting lives
> in **xrtm-train**. See the [Evaluation API](api/evaluation.md).

- **Execution Trace**: which execution-graph stages were involved in this decision?
- **Reasoning Trace**: what assumptions were made inside the forecast result? (`ForecastOutput.logical_trace` / `reasoning_trace`)

---

## Directory Map

- `src/xrtm/forecast/core/`: the execution engine, interfaces, and runtime physics (Orchestrator, Runtime, Guardian).
- `src/xrtm/forecast/kit/`: the applied layer (agents, skills, topologies, and pipeline helpers).
- `src/xrtm/forecast/providers/`: The Hardware Layer (Inference, Decisions, Tools).

## Public API Boundaries

- `xrtm.forecast` is the stable convenience surface for orchestration primitives and assistant factories.
- `xrtm.forecast.kit` is a namespace entrypoint; prefer importing concrete agents, topologies, and sentinels from their subpackages.
- `xrtm.forecast.providers.inference` is the stable home for provider configuration and factory access.

Legacy convenience imports remain available for compatibility, but new code should prefer the narrower paths above.

---

## Class Dependency Diagram

The following diagram shows the relationship between Core ABCs and their implementations:

```mermaid
classDiagram
    direction TB

    %% CORE LAYER (Abstract Base Classes)
    class InferenceProvider {
        <<abstract>>
        +generate_content_async()
        +generate_content()
        +stream()
        +knowledge_cutoff
    }
    class DecisionProvider {
        <<abstract>>
        +decide(state, options)
    }
    class HumanProvider {
        <<abstract>>
        +get_human_input(prompt)
    }
    class FactStore {
        <<abstract>>
        +remember(fact)
        +query(subject)
        +forget(subject)
    }
    class Tool {
        <<abstract>>
        +name
        +description
        +run()
        +pit_supported
    }
    class Agent {
        <<abstract>>
        +run()
        +add_skill()
        +set_fact_store()
    }

    %% PROVIDERS LAYER (Implementations)
    class OpenAIProvider {
        +model_id
        +base_url
        +rate_limiter
    }
    class AnthropicProvider {
        +model_id
    }
    class MockProvider {
        +seed
    }
    class LLMDecisionProvider {
        +model
    }
    class JevProvider {
        +answer_key
    }
    class TavilySearchTool {
        +api_key
    }
    OpenAIProvider --|> InferenceProvider
    AnthropicProvider --|> InferenceProvider
    MockProvider --|> InferenceProvider
    LLMDecisionProvider --|> DecisionProvider
    JevProvider --|> LLMDecisionProvider
    TavilySearchTool --|> Tool

    %% KIT LAYER (Agents, Topologies, Decisions)
    class LLMAgent {
        +model
        +parse_output()
    }
    class GraphAgent {
        +orchestrator
    }
    class ForecastingAnalyst {
        +prompt_template
        +structured_output
        +strict_parse
    }
    class RoutingAgent {
        +fast_tier
        +smart_tier
    }
    class EscalationRouter {
        +confidence_threshold
    }
    LLMAgent --|> Agent
    GraphAgent --|> Agent
    ForecastingAnalyst --|> LLMAgent
    RoutingAgent --|> Agent
    EscalationRouter --|> DecisionProvider

    %% RELATIONSHIPS
    Agent --> FactStore : uses
    LLMAgent --> InferenceProvider : uses
    ForecastingAnalyst --> Tool : uses
```

> Scoring/calibration evaluators (`BrierScoreEvaluator`,
> `ExpectedCalibrationErrorEvaluator`) live in **xrtm-eval**; backtesting lives
> in **xrtm-train**. See the [Evaluation API](api/evaluation.md).

### Key Architectural Rules

1. **Core never imports Kit**: ABCs in `core/` cannot depend on implementations in `kit/`.
2. **Providers are interchangeable**: Any `InferenceProvider` can be swapped without changing agent code.
3. **FactStore enables institutional memory**: Agents can optionally connect to a `FactStore` via `set_fact_store()`.
