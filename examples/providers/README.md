# Providers Examples (Connectors)

These examples demonstrate how to connect `xrtm-forecast` to external data sources and LLM backends.

## Projects

### [provider_free_analyst](file:///workspace/forecast/examples/providers/provider_free_analyst/run_provider_free_analyst.py)
⭐ **Start here** — Use the DeterministicProvider to test and learn XRTM without API keys. Perfect for testing, CI/CD, and rapid iteration.

### [inference_direct](file:///workspace/forecast/examples/providers/inference_direct/run_inference_direct.py)
Direct interaction with inference providers (Gemini, Vertex AI, etc.) outside of a graph.

### [minimal_inference](file:///workspace/forecast/examples/providers/minimal_inference/run_minimal_inference.py)
Minimal example showing the lowest-level provider interface.

### [tool_wrapping](file:///workspace/forecast/examples/providers/tool_wrapping/run_tool_wrapping.py)
How to wrap external Python tools and APIs for use by agents.

### [data](file:///workspace/forecast/examples/providers/data/)
Implementations for specific data retrieval and storage backends.

## Related Documentation

- **[Provider-Free Testing Guide](../../docs/provider-free-testing.md)**: Comprehensive guide to testing without API keys
