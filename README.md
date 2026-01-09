# xrtm-forecast

Institutional-grade parallelized agentic reasoning engine.

## Overview
`xrtm-forecast` is an institutional-grade, domain-agnostic intelligence engine. It provides a framework for:
- **Inference Layer**: Standardized provider interfaces for Gemini, OpenAI, and **local Hugging Face models**.
- **Tiered Reasoning**: Composite `RoutingAgent` for cost-optimized task dispatching.
- **Reasoning Graph**: A pluggable state-machine orchestrator for multi-agent workflows.
- **Agent Core**: Standardized `Agent` base class for structured reasoning and parsing.
- **Skill Protocol**: Composable behaviors (e.g., Search, **SQL**, **Pandas**) that agents can dynamically equip.
- **Observability**: OTel-native structured telemetry and institutional execution reports.
- **Evaluation**: Built-in **Backtest Engine** for large-scale accuracy metrics (Brier Score, ECE).
- **Temporal Sandboxing**: Multi-layered protection (PiT Tools, Clock Mocking, Leakage Guardian) to prevent look-ahead bias in historical backtests.

## Architectural Design: "Pure Core / The Kit"

`xrtm-forecast` is designed for modularity using a strict three-tier architecture:
- **The Core (`/core`)**: Zero-dependency protocol layer and state-machine orchestrator.
- **The Kit (`/kit`)**: Importable "Instruments" (Agents, Skills, Evaluators) for standard use cases.
- **Providers (`/providers`)**: Concrete connectors for cloud and local inference backends.

## Installation

### From PyPI (Stable)
```bash
# Standard Institutional Install (Cloud + Core)
pip install xrtm-forecast

# Hardware-Specific Local Inference
pip install "xrtm-forecast[transformers]"  # PyTorch + HuggingFace
pip install "xrtm-forecast[vllm]"          # High-throughput serving
pip install "xrtm-forecast[llama-cpp]"     # CPU-optimized GGUF
pip install "xrtm-forecast[xlm]"           # Local Encoder specialists

# Researcher Kit (Enhanced Data/Viz)
pip install "xrtm-forecast[data,viz,memory]"
```

### From Source (Latest)
```bash
pip install git+https://github.com/xrtm-org/forecast.git
```

## Configuration

`xrtm-forecast` follows a decentralized configuration pattern. Global environment variables are used for infrastructure (API keys), while specific behaviors are controlled via module-level configuration classes.

### 1. Environment Secrets

Set your API keys in a `.env` file or environment:

```bash
# Core API Keys
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

### 2. Component Configuration

Each major module (`inference`, `graph`, `telemetry`, `tools`) has its own `config.py` defining its schema. This allows you to instantiate multiple components with different settings in the same process.

## Quick Start

`xrtm-forecast` is designed for high-end ergonomics. Use the pre-configured assistants to start forecasting in seconds:

```python
import asyncio
from forecast import create_forecasting_analyst

async def main():
    # 1. Instantiate the analyst with a shortcut
    # (API keys are automatically injected from your .env file)
    agent = create_forecasting_analyst(model_id="gemini")
    
    # 2. Execute reasoning on a complex probabilistic question
    result = await agent.run(
        "Will a general-purpose AI (AGI) be publicly announced before 2030?"
    )
    
    print(f"Confidence: {result.confidence}")
    print(f"Reasoning: {result.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Documentation & Examples

- **Architecture**: [The "Lego" Design](docs/architecture.md)
- **Agent Registry**: [Pre-built & Core Agents](docs/agents_registry.md)
- **Examples**: Check the [examples/](examples/) directory:
    - [examples/kit/minimal_agent.py](examples/kit/minimal_agent.py): One-line agent setup.
    - [examples/kit/local_analyst.py](examples/kit/local_analyst.py): Private reasoning with HF models.
    - [examples/kit/features/tiered_reasoning.py](examples/kit/features/tiered_reasoning.py): Optimal routing between Fast/Smart tiers.
    - [examples/kit/features/enterprise_data.py](examples/kit/features/enterprise_data.py): Integrated SQL and Pandas analytics.
    - [examples/kit/features/discovery.py](examples/kit/features/discovery.py): Dynamic skill discovery.
    - [examples/kit/backtest_workflow.py](examples/kit/backtest_workflow.py): Historical backtesting with temporal sandboxing.

## Contributing

We welcome institutional-grade contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and our development workflow.


---

## License

`xrtm-forecast` is open-source software licensed under the **Apache-2.0** license. See the [LICENSE](LICENSE) file for more details.

Copyright © 2026 XRTM Team.
