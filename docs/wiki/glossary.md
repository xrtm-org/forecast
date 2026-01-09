# Glossary & Terminology

This glossary defines the "Institutional Language" used throughout the `xrtm-forecast` ecosystem. It is designed to be the single source of truth for developers and users.

## Core Entities

### **Agent**
An autonomous software entity capable of perceiving context, reasoning via an LLM, and executing actions.
*   *See*: [Concepts > Agents](concepts/agents.md)
*   *Code*: `forecast.kit.agents.Agent`

### **Tool**
A granular, low-level Python function that performs a single action.
*   *Analogy*: A hammer.
*   *Code*: Any function wrapped by `FunctionTool`.

### **Skill**
A high-level **Capability** that often bundles several tools and specific logic for a domain.
*   *Analogy*: Carpentry (the ability to use hammer, saw, and nails to build a table).
*   *Examples*: `SQLSkill` (bundles connection logic, security checks, and query tools).

### **Capability**
An abstract interface allowing an Agent to acquire context from the outside world.

---

## Integration Patterns

Often, a single piece of logic (like a "Statistical Model" or "Market Fetcher") can be used in two different ways. The choice depends on **who is in charge**.

### **The Instrument Pattern (Skill/Tool)**
The **Agent** is in charge. It decides *when* and *if* to call the logic during its reasoning loop.
*   *Analogy*: A surgeon (Agent) using a scalpel (Tool).

### **The Station Pattern (Stage)**
The **Orchestrator** is in charge. The logic runs automatically as a mandatory step in the workflow process.
*   *Analogy*: An assembly line (Graph) where an item moves to a station (**Stage**).

---

## Orchestration Engine

### **Orchestrator**
The state-machine engine that manages the workflow.
*   *See*: [Concepts > Orchestration](concepts/orchestration.md)
*   *Code*: `forecast.core.orchestrator.Orchestrator`

### **GraphState**
The shared memory object passed between **Stages** during execution.
*   *See*: [Concepts > Orchestration](concepts/orchestration.md#graphstate)

### **Stage**
A single step in a workflow (implemented as a `Node` in the engine).
*   *See*: [Concepts > Orchestration](concepts/orchestration.md#stages-the-functional-slots)

### **Parallel Group**
A set of **Stages** that execute at the same time (concurrently).
*   *See*: [Concepts > Orchestration](concepts/orchestration.md#parallel-groups)

### **Topology**
A pre-defined, reusable pattern of **Stages** and Edges.
*   *See*: [Patterns > Topologies](patterns/topologies.md)
*   *Code*: `forecast.kit.patterns`

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
