# Glossary & Terminology

This glossary defines the "Institutional Language" used throughout the `xrtm-forecast` ecosystem. It is designed to be the single source of truth for developers and users.

## Core Entities

### **Agent**
An autonomous software entity capable of perceiving context, reasoning via an LLM, and executing actions.
*   *See*: [Concepts > Agents](concepts/agents.md)
*   *Code*: `forecast.agents.Agent`

### **Tool (or Skill)**
A specific, executable function that an Agent can use.
*   *See*: [Concepts > Tools](concepts/tools.md)
*   *Code*: `forecast.tools.Tool`

### **Capability**
An abstract interface allowing an Agent to acquire context from the outside world.
*   *See*: [Concepts > Tools](concepts/tools.md)

---

## Orchestration Engine

### **Orchestrator**
The state-machine engine that manages the workflow.
*   *See*: [Concepts > Orchestration](concepts/orchestration.md)
*   *Code*: `forecast.graph.orchestrator.Orchestrator`

### **GraphState**
The shared memory object passed between nodes during execution.
*   *See*: [Concepts > Orchestration](concepts/orchestration.md#graphstate)

### **Node**
A single step in a workflow.
*   *See*: [Concepts > Orchestration](concepts/orchestration.md#nodes)

### **Parallel Group**
A set of Nodes that execute at the same time (concurrently).
*   *See*: [Concepts > Orchestration](concepts/orchestration.md#parallel-groups)

### **Topology**
A pre-defined, reusable pattern of Nodes and Edges.
*   *See*: [Patterns > Topologies](patterns/topologies.md)
*   *Code*: `forecast.graph.topologies`

---

## Infrastructure

### **Inference Provider**
The adapter layer connecting `xrtm-forecast` to an LLM backend.
*   *See*: [Standards > Streaming](standards/streaming.md)

### **Symmetry**
The guarantee that your code works exactly the same way whether using a cloud model or a local model.
*   *See*: [Standards > Streaming](standards/streaming.md#local-streaming-hugging-face)

### **Telemetry (OTel)**
The system for recording logs, traces, and metrics in a standard format.
*   *Analogy*: The flight recorder (Black Box).
