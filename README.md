# xrtm-forecast

Institutional-grade parallelized agentic reasoning engine.

## Overview
`xrtm-forecast` is the core intelligence engine originally developed for the CAFE (Computer-Aided Financial Engineering) platform. It provides a domain-agnostic framework for:
- **Inference Layer**: Standardized provider interfaces for Gemini and OpenAI.
- **Reasoning Graph**: A pluggable state-machine orchestrator for multi-agent workflows.
- **Agent Core**: Standardized `Agent` base class for structured reasoning and parsing.
- **Skill Protocol**: Composable behaviors (e.g., Search) that agents can dynamically equip.
- **Observability**: OTel-native structured telemetry and institutional execution reports.
- **Evaluation**: Built-in harness for backtesting and accuracy metrics (Brier Score).

## Architectural Design: "Engine vs. Specialists"

`xrtm-forecast` is designed for modularity using a "Lego" philosophy:
- **The Engine (`agents/`)**: Core structural bricks like `LLMAgent` and `ToolAgent`.
- **The Specialists (`agents/specialists/`)**: Pre-built expert roles like the `ForecastingAnalyst`.
- **The Registry**: A central exchange for discovering and plugging in agents and tools.

For a deep dive, see [Architecture & Design Principles](docs/architecture.md).

## Installation

### From PyPI (Stable)
```bash
pip install xrtm-forecast

# With extras (redis, memory)
pip install "xrtm-forecast[redis,memory]"
```

### From Source (Latest)
```bash
pip install git+https://github.com/xrtm-org/forecast.git
```

## Configuration

`xrtm-forecast` implements an institutional-grade configuration system that automatically selects the appropriate inference provider based on your environment. Pro-actively set your API keys in a `.env` file:

```bash
# Provider Keys
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Optional: Explicitly force a provider (defaults to GEMINI if keys are present)
# PRIMARY_PROVIDER=OPENAI 
```

## Quick Start

`xrtm-forecast` is an abstract engine. To run a forecast, you provide your own configuration and model choice.

```python
import asyncio
from forecast.agents.specialists import ForecastingAnalyst
from forecast.inference.factory import ModelFactory
from forecast.inference.config import GeminiConfig

async def main():
    # 1. Provide your model configuration
    config = GeminiConfig(model_id="gemini-2.0-flash")
    
    # 2. Instantiate the provider and agent
    model = ModelFactory.get_provider(config)
    agent = ForecastingAnalyst(model=model)
    
    # 3. Execute reasoning on a complex probabilistic question
    result = await agent.run(
        "Will a general-purpose AI (AGI) be publicly announced before 2030?"
    )
    
    print(f"Confidence: {result.confidence * 100}%")
    print(f"Reasoning: {result.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Documentation & Examples

- **Architecture**: [The "Lego" Design](docs/architecture.md)
- **Agent Registry**: [Pre-built & Core Agents](docs/agents_registry.md)
- **Examples**: Check the [examples/](examples/) directory:
    - [examples/minimal_agent.py](examples/minimal_agent.py): One-line agent setup.
    - [examples/features/discovery.py](examples/features/discovery.py): Dynamic skill discovery.
    - `pipelines/`: End-to-end multi-agent workflows.

## Contributing

We welcome institutional-grade contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and our development workflow.


---

## License

`xrtm-forecast` is open-source software licensed under the **Apache-2.0** license. See the [LICENSE](LICENSE) file for more details.

Copyright © 2026 XRTM Team.
