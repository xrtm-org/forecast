# Inference
1. **Cloud-Native**: Using `standard` install.
2. **Local-First**: Using specific hardware extras (e.g., `transformers`, `vllm`).

```bash
# Cloud Providers
pip install "xrtm-forecast[standard]"

# Local Providers
pip install "xrtm-forecast[vllm]"
```

::: forecast.providers.inference.base.InferenceProvider
    options:
      show_root_heading: true
::: forecast.providers.inference.base.ModelResponse
    options:
      show_root_heading: true
