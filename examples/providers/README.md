# Providers Examples (Connectors)

These examples demonstrate how to connect `xrtm-forecast` to external data sources and LLM backends.

**Quick chooser:** if you want the released provider-free first run, start with `xrtm`; if you want to wire forecasting into code, start with the examples below.

## Projects

### [provider_free_analyst](./provider_free_analyst/)
⭐ **Start here** — use the DeterministicProvider to test and learn XRTM without API keys. Install `xrtm==0.7.0` (or an editable checkout of the product package) first, because the provider lives in `xrtm.product.providers`.

### [inference_direct](./inference_direct/)
Direct interaction with inference providers (Gemini, Vertex AI, etc.) outside the execution graph.

### [minimal_inference](./minimal_inference/)
Minimal example showing the lowest-level provider interface.

### [tool_wrapping](./tool_wrapping/)
How to wrap external Python tools and APIs for use by agents.

### [data](./data/)
Implementations for specific data retrieval and storage backends.

## Related documentation

- **[Provider-Free Testing Guide](../../docs/provider-free-testing.md)**: comprehensive guide to testing without API keys.
