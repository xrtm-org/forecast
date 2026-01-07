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

`xrtm-forecast` relies on environment variables for API keys and service connections. Create a `.env` file in your project root:

```bash
GEMINI_API_KEY=your_key_here
REDIS_URL=redis://localhost:6379/0  # Optional (fallback to in-memory)
```

## Quick Start: Inference

```python
import asyncio
from forecast import ModelFactory
from forecast.inference.config import GeminiConfig
from pydantic import SecretStr

async def main():
    config = GeminiConfig(
        api_key=SecretStr("your-key"), 
        model_id="gemini-2.0-flash-lite"
    )
    provider = ModelFactory.get_provider(config)
    response = await provider.generate_content_async("What is the causality of inflation?")
    print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
```

## Documentation & Examples

- **Architecture**: [The "Lego" Design](docs/architecture.md)
- **Agent Registry**: [Pre-built & Core Agents](docs/agents_registry.md)
- **Examples**: Check the [examples/](examples/) directory for structured entry points:
    - `core/`: Basic library usage.
    - `features/`: Specialized modules (Skills, Eval, Telemetry).
    - `pipelines/`: End-to-end multi-agent workflows.

## Contributing

We welcome institutional-grade contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and our development workflow.


---

## License

`xrtm-forecast` is open-source software licensed under the **Apache-2.0** license. See the [LICENSE](LICENSE) file for more details.

Copyright © 2026 XRTM Team.
