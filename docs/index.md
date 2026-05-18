# xrtm-forecast

Institutional-grade runtime for auditable forecast runs.

## Overview

`xrtm-forecast` supplies the code-level execution graph, reasoning instrumentation, and provider boundaries behind XRTM forecasting.

## Terminology quick map

- **Workflow**: a released user journey in the top-level `xrtm` product.
- **Run**: one concrete execution of the forecast runtime.
- **Execution graph**: the orchestrator DAG of nodes and edges that drives a run.
- **Reasoning trace**: the narrative plus reasoning graph recorded in `ForecastOutput`.
- **Topology**: a reusable pattern for wiring an execution graph.
- **Pipeline**: a pre-assembled helper that builds a forecast path from one or more stages or topologies.

## Key Features

- **Sequential & Parallel Orchestration**: manage execution-graph stages with a robust state machine.
- **Unified Memory**: provider-agnostic interface for episodic and semantic memory using vector stores.
- **Provider-Agnostic Inference**: standardized interactions with Gemini, OpenAI, and other LLMs.
- **Audit-First Design**: every reasoning trace and execution trace can be logged, hashed, and signed.
- **Institutional Scale**: built for speed and consistency using `uv` and Docker.
