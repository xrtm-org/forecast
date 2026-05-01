# Provider-Free Analyst

**Script**: `run_provider_free_analyst.py`

Demonstrates using the DeterministicProvider for testing and learning XRTM without API keys.

## Usage

```bash
# From repository root
python forecast/examples/providers/provider_free_analyst/run_provider_free_analyst.py
```

## What This Shows

- How to import and instantiate the DeterministicProvider
- Using provider-free backends with ForecastingAnalyst
- Inspecting cache statistics
- Running multiple forecasts deterministically

## Concepts

- **DeterministicProvider**: A test double that returns structured, deterministic forecasts without API calls
- **Provider Abstraction**: The same agent code works with any provider (cloud or mock)
- **Cache Semantics**: Provider-free mode maintains cache statistics for testing

## Expected Output

The script runs three forecasts and displays:
- Model identification (xrtm-deterministic-product)
- Confidence scores (deterministic probabilities)
- Reasoning snippets
- Cache statistics (hits, misses, hit rate)

## Why Provider-Free?

This example is perfect for:
- **Learning**: Explore XRTM concepts without setup friction
- **Testing**: Write deterministic tests that don't call external APIs
- **CI/CD**: Run validation pipelines that are fast and free
- **Development**: Iterate on agent logic without API costs

## Related

- **[Provider-Free Testing Guide](../../../docs/provider-free-testing.md)**: Comprehensive guide to testing without API keys
- **[Minimal Inference](../minimal_inference/)**: Lower-level provider interface examples
- **[Getting Started](../../../../xrtm/docs/getting-started.md)**: CLI quickstart with provider-free demos
