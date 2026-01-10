# Local Analyst

**Script**: `run_local_analyst.py`

This example demonstrates how to run a forecasting agent using a local Small Language Model (SLM) via a provider like Ollama or LocalAI, instead of a cloud-based API.

## Usage

```bash
# From repository root
python3 examples/kit/local_analyst/run_local_analyst.py
```

## Prerequisities
- A local inference server running (e.g., Ollama).
- `OPENAI_BASE_URL` environment variable pointing to your local server (default: `http://localhost:11434/v1`).

## Concepts
- **Privacy-First Inference**: Running reasoning chains without data leaving your machine.
- **Custom Base URLs**: Configuring the provider to talk to non-standard endpoints.
