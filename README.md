# xrtm-forecast v0.7.0

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**The Runtime Engine for XRTM.**

`xrtm-forecast` provides the agents, providers, topologies, and orchestration to build AI forecasting systems. It's a composable framework — import the pieces you need and wire them together.

## Installation

```bash
pip install xrtm-forecast
```

## Quick Start

```python
from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.providers.inference.factory import ModelFactory

# Use any OpenAI-compatible endpoint

[![PyPI](https://img.shields.io/pypi/v/xrtm-forecast?style=flat-square)](https://pypi.org/project/xrtm-forecast/)

config = OpenAIConfig(
    model_id="your-model",
    base_url="$OPENAI_BASE_URL",
    api_key="your-api-key",
)
provider = ModelFactory.get_provider(config)
analyst = ForecastingAnalyst(model=provider, name="forecaster")

# Ask a forecasting question
from xrtm.data import ForecastQuestion
question = ForecastQuestion(
    id="fed-march-2025",
    title="Will the Fed raise rates in March 2025?",
)
forecast = await analyst.run(question)
print(f"Probability: {forecast.probability:.2f}")
```

## What's Included

### OpenAI-compatible Provider
One provider that works with any OpenAI-compatible API: any OpenAI-compatible endpoint. Set `base_url` to point anywhere.

### Agents
- **`ForecastingAnalyst`** — Full forecast agent: structured prompts, causal reasoning traces, JSON output parsing
- **`LLMAgent`** — Base agent with tool retrieval, output parsing
- **`RoutingAgent`** — FAST/SMART tiered routing for cost optimization
- **`ToolAgent`** / **`GraphAgent`** — Wrap functions or sub-graphs as agents

### Topologies
Composable multi-agent patterns in `kit/topologies/`:
- **`RecursiveConsensus`** — Parallel analysts → aggregate → supervisor → loop
- **`create_debate_graph()`** — Pro/Con/Judge debate pattern
- **`create_fanout_graph()`** — Parallel workers → aggregator

### Orchestration
- **`Orchestrator`** — DAG state machine for workflow graphs
- **`AsyncRuntime`** — Chronos-aware async runtime

### Infrastructure
- **`InferenceCache`** — SQLite cache for LLM responses (enabled by default)
- **Retry with backoff** — 2 retries on API errors
- **`LeakageGuardian`** — Temporal leakage prevention for backtests

## XRTM Ecosystem

Part of the XRTM forecasting stack:

| Package | Role | Version |
|---------|------|---------|
| `xrtm-data` | Schemas & question sources | 0.3.0 |
| `xrtm-eval` | Scoring (Brier, ECE, LogScore) | 0.3.0 |
| `xrtm-forecast` | Runtime engine (this package) | 0.7.0 |
| `xrtm-train` | Backtesting & optimization | 0.3.0 |
| `xrtm` | Product CLI | 0.9.0 |

## License

Apache 2.0
