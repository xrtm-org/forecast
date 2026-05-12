# Local Analyst

**Script**: `run_local_analyst.py`

This example demonstrates how to run a forecasting agent against a local OpenAI-compatible inference server, such as llama.cpp server, Ollama, or LocalAI, instead of a cloud API.

## Usage

```bash
# From repository root
python3 examples/kit/local_analyst/run_local_analyst.py
```

## Prerequisites

- A local OpenAI-compatible inference server.
- For the local workspace profile:
  - start `/home/moy/workspaces/local-claude-llamacpp` with `./manage.sh start`
  - use base URL `http://localhost:8080/v1`
  - use model id `Qwen3.5-9B-UD-Q4_K_XL.gguf`

## Local smoke test

```bash
cd /home/moy/workspaces/xrtm
./workspace.sh local-llm-start
./workspace.sh check-local-llm
./workspace.sh local-llm-stop
```

## Concepts
- **Privacy-First Inference**: Running reasoning chains without data leaving your machine.
- **Custom Base URLs**: Configuring the provider to talk to non-standard endpoints.
- **OpenAI-Compatible Provider**: XRTM uses `OpenAIConfig(base_url="http://localhost:8080/v1")` for llama.cpp server; the separate `LlamaCppProvider` is for in-process GGUF loading.

## Why this is an honest advanced path

Use this after you have already proven the provider-free control path.

- the provider-free baseline gives you a deterministic reference point
- a local analyst run is a real candidate change that can produce different probabilities, scores, and costs
- compare it against the control on the same question set before calling it an improvement
- keep the candidate only if the quality gain justifies the added runtime and model-serving complexity
