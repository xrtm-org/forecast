# Agents

An Agent is the primary "actor" in the `xrtm-forecast` system. It simulates a human analyst or worker.

## Anatomy of an Agent
An Agent connects three components:

1.  **Persona (`role`/`name`)**:
    *   Defines the "Identity".
    *   Example: "You are a Senior Risk Officer."
2.  **Model (`InferenceProvider`)**:
    *   Defines the "Brain".
    *   Example: GPT-4o, Claude 3.5 Sonnet, or Llama-3-8B (Local).
3.  **Context**:
    *   The memory state (passed via `GraphState`).

## Instantiation
```python
from forecast.kit.agents import LLMAgent
from forecast.providers.inference.openai_provider import OpenAIProvider

provider = OpenAIProvider(api_key="...")
agent = LLMAgent(model=provider, name="Alice", role="Researcher")
```

## Lifecycle
1.  **Input**: Receives a task/message.
2.  **Reasoning**: Uses LLM to decide on actions (Tools) or answer.
3.  **Output**: Returns a result or tool call.

## Shapes vs. Roles (Architecture)

To maintain a lean engine, we distinguish between structural abstractions and specialist personas:

1.  **Abstractions (The "Shapes")**: Mechanical building blocks like `LLMAgent` (reasoning), `ToolAgent` (execution), and `GraphAgent` (recursion).
2.  **Specialists (The "Roles")**: Pre-assembled kits like `ForecastingAnalyst` (Bayesian reasoning) or `FactCheckerAgent` (NLI verification).

## Agents as Stages
While an Agent is an object, it is often consumed as a Stage in an Orchestrator graph. 

We use **Topologies** (like `RecursiveConsensus`) to wrap agents automatically so they can communicate via the `GraphState`.

*   **One Brain, Many Slots**: You can use the same Agent object in multiple different Stages (e.g., as a "Debater" and then as a "Summary Writer").
*   **Context Passing**: When an Agent runs as a Stage, it reads its input from `state.context` and writes its results back to it.
