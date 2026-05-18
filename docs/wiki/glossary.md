# Glossary & Terminology

This glossary is the forecast-runtime source of truth for XRTM terminology.

## Product vs runtime

### Workflow
A released, user-facing journey in the top-level `xrtm` product (for example the provider-free first-success path).

### Run
One concrete execution of `xrtm-forecast` for a forecast request.

## Execution layer

### Execution graph
The orchestrator DAG that moves state through a run.
*Code*: `forecast.core.orchestrator.Orchestrator`

### Node
The engine's registered execution unit. Nodes are what the orchestrator schedules.

### Stage
The role a node plays in an execution graph. A stage is the documentation-facing term; a node is the engine-facing term.

### Parallel group
A named set of nodes that execute concurrently before the run continues.

### Topology
A reusable pattern for wiring nodes and edges into an execution graph.
*Code*: `forecast.kit.patterns`, `forecast.kit.topologies.*`

### Pipeline
A pre-assembled helper that builds or runs a forecast path from one or more stages or topologies. Some module and directory names keep `pipeline` for compatibility.

### Graph state
The shared state object passed through an execution graph.
*Code*: `forecast.core.schemas.graph.BaseGraphState`

### Execution trace
The ordered record of nodes visited during a run. In runtime state this is stored as `execution_path`, with `execution_trace` as the preferred user-facing alias.

## Reasoning layer

### Reasoning trace
The forecast rationale plus its serialized reasoning graph. In `ForecastOutput`, `reasoning_trace` is the canonical serialized view; `reasoning`, `logical_trace`, and `logical_edges` remain compatibility inputs and legacy mirrored properties.

### Reasoning graph
The causal or logical structure inside a reasoning trace. Current serialized compatibility payloads may still use the nested key `causal_graph`.

### Agent
An autonomous software entity capable of perceiving context, reasoning via an LLM, and executing actions.
*See*: [Concepts > Agents](concepts/agents.md)
*Code*: `forecast.kit.agents.Agent`

### Tool
A granular, low-level Python function that performs one action.

### Skill
A higher-level capability that bundles tools and domain logic.
