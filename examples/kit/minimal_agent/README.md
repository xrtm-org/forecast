# Minimal Agent

**Script**: `run_minimal_agent.py`

The "Hello World" of `xrtm-forecast` agents. This example demonstrates the simplest possible instantiation of an LLM agent—no memory, no tools, just a direct prompt-response loop.

## Usage

```bash
# From repository root
python3 examples/kit/minimal_agent/run_minimal_agent.py
```

## Concepts
- **LLMAgent**: The base class for all agents.
- **InferenceProvider**: Connecting the agent to a model backend.
- **Direct Interaction**: Sending a user message and receiving a response.
