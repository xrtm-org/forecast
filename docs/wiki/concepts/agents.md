# Agents

An **Agent** is the primary "actor" in the `xrtm-forecast` system. It simulates a human analyst or worker.

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
from forecast.agents import LLMAgent
from forecast.inference.openai_provider import OpenAIProvider

provider = OpenAIProvider(api_key="...")
agent = LLMAgent(model=provider, name="Alice", role="Researcher")
```

## Lifecycle
1.  **Input**: Receives a task/message.
2.  **Reasoning**: Uses LLM to decide on actions (Tools) or answer.
3.  **Output**: Returns a result or tool call.
