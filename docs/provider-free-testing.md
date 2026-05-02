# Provider-Free Testing Guide

This guide shows you how to use XRTM without API keys, cloud dependencies, or hosted LLM services.

**⭐ Start here**: Provider-free mode is the recommended path for getting started, testing, and learning XRTM.

Install the top-level product package once so the shipped CLI and `DeterministicProvider` are available:

```bash
pip install xrtm==0.3.0
```

## Why Provider-Free?

Provider-free mode is perfect for:

- **Learning**: Explore XRTM concepts without setup friction
- **Testing**: Write deterministic tests that don't call external APIs
- **CI/CD**: Run validation pipelines that are fast, repeatable, and free
- **Development**: Iterate on agent logic without burning API credits

**Zero service prerequisites.** No API keys, no model downloads, no server setup.

**Instant start after install.** Run `xrtm demo --provider mock --limit 2` and you're forecasting.

---

## Decision Guide: Mock vs Local-LLM

Choose your inference path based on your goal:

### Use `--provider mock` when:
✅ **Learning XRTM** for the first time  
✅ **Testing agent logic** without LLM variability  
✅ **Running CI/CD pipelines** that need deterministic results  
✅ **Benchmarking performance** without network latency  
✅ **Iterating rapidly** without API costs or rate limits  
✅ **You want to start immediately** with zero setup  

**Setup time**: 0 seconds  
**Prerequisites**: None

### Use `--provider local-llm` when:
⚠️ **Testing real LLM reasoning** behavior  
⚠️ **Privacy-sensitive deployments** (data never leaves your machine)  
⚠️ **Offline operation** requirements  
⚠️ **Evaluating specific model** capabilities  

**Setup time**: 30-60 minutes for first-time setup  
**Prerequisites**:
- Local OpenAI-compatible server (llama.cpp, Ollama, LocalAI)
- Downloaded model weights (multi-GB files)
- GPU with sufficient VRAM (8GB+ recommended)
- Understanding of model context length and token budgets

**Recommendation**: Start with `--provider mock`. Only switch to `local-llm` when you specifically need real LLM behavior and have completed the server setup.

---

## What is Provider-Free Mode?

Provider-free mode uses the **DeterministicProvider**, a mock inference provider that:

- Returns structured, deterministic responses based on input hashing
- Requires no API keys or network calls
- Produces realistic forecast outputs (probabilities, reasoning, traces)
- Maintains cache statistics for performance testing
- Completes in milliseconds, not seconds

The DeterministicProvider generates forecasts by:
1. Hashing the input prompt to create a stable seed
2. Deriving a probability in the range [0.05, 0.95]
3. Constructing a valid forecast response with reasoning and traces

This ensures:
- **Repeatability**: Same input always produces same output
- **Validity**: Outputs match the expected forecast schema
- **Speed**: No network latency or model inference time
- **Safety**: No API costs, rate limits, or quota concerns

---

## CLI Usage (Product Shell)

The `xrtm` CLI provides the highest-level interface for provider-free testing.

### Quick Start

Run a complete forecasting pipeline locally:

```bash
xrtm demo --provider mock --limit 2
```

This:
- Loads 2 questions from the embedded corpus
- Generates forecasts using the mock provider
- Evaluates forecast quality with Brier scores
- Writes a complete run directory under `runs/`

**Expected runtime**: < 5 seconds

### Reusable Profiles

Save your provider-free settings in a profile:

```bash
xrtm profile create local-mock --provider mock --limit 2 --runs-dir runs
xrtm run profile local-mock
```

Profiles are stored under `.xrtm/profiles/` and can be reused across sessions.

### Performance Testing

Use provider-free mode for deterministic performance benchmarks:

```bash
xrtm perf run \
  --scenario provider-free-smoke \
  --iterations 3 \
  --limit 10 \
  --runs-dir runs-perf \
  --output performance.json
```

This measures pipeline performance without network variability.

---

## Library Usage (Python API)

For programmatic usage and complete API documentation, see the **[Python API Reference](../../xrtm/docs/python-api-reference.md)**.

### Quick Library Example

```python
import asyncio
from xrtm.forecast import ForecastingAnalyst
from xrtm.product.providers import DeterministicProvider

async def main():
    # Provider-free backend
    provider = DeterministicProvider()
    agent = ForecastingAnalyst(model=provider)
    
    # Run a forecast
    result = await agent.run("Will AGI be announced before 2030?")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Reasoning: {result.reasoning}")

asyncio.run(main())
```

See the [Python API Reference](../../xrtm/docs/python-api-reference.md) for:
- Complete API surface documentation
- Advanced usage patterns
- Integration with the product shell
- Custom provider implementations

### Monitoring

Create and test monitors without API calls:

```bash
xrtm monitor start --provider mock --limit 2 --runs-dir runs
xrtm monitor run-once runs/<run-id>
```

### WebUI Smoke Testing

Launch the WebUI with provider-free data:

```bash
xrtm demo --provider mock --limit 5
xrtm web --runs-dir runs --smoke
```

---

## Library Usage (`xrtm-forecast` + `xrtm`)

Provider-free library workflows combine the `xrtm-forecast` agent/runtime APIs with the top-level `xrtm` product package, which ships the `DeterministicProvider`.

### Import the Provider

```python
from xrtm.product.providers import DeterministicProvider
```

The DeterministicProvider is part of the product layer (`xrtm.product.providers`), not the standalone `xrtm-forecast` wheel. This is intentional—it's a testing utility, not a production inference backend.

### Basic Usage

```python
from xrtm.product.providers import DeterministicProvider
from xrtm.forecast.providers.inference.base import ModelResponse

# Create the provider
provider = DeterministicProvider()

# Generate a forecast
prompt = "Will the S&P 500 close above 5,000 by end of 2026?"
response: ModelResponse = provider.generate_content(prompt)

print(f"Response: {response.text}")
print(f"Usage: {response.usage}")
print(f"Metadata: {response.metadata}")
```

**Output structure**:
```json
{
  "probability": 0.732,
  "reasoning": "Deterministic provider-free forecast for <question-id>.",
  "logical_trace": [...],
  "structural_trace": [...]
}
```

### Async Usage

The DeterministicProvider supports async calls:

```python
import asyncio
from xrtm.product.providers import DeterministicProvider

async def main():
    provider = DeterministicProvider()
    response = await provider.generate_content_async(
        "Will AGI be announced before 2030?"
    )
    print(response.text)

asyncio.run(main())
```

### Using with Agents

Replace any cloud provider with the DeterministicProvider:

```python
from xrtm.product.providers import DeterministicProvider
from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst

# Create the provider-free agent
provider = DeterministicProvider()
agent = ForecastingAnalyst(model=provider)

# Run the agent
result = await agent.run("Will inflation exceed 3% in 2026?")
print(f"Confidence: {result.confidence}")
print(f"Reasoning: {result.reasoning}")
```

### Adapting Examples

Most examples in `forecast/examples/` use cloud providers (Gemini, OpenAI). To adapt them for provider-free testing:

**Before** (requires API key):
```python
from xrtm.forecast.core.config.inference import GeminiConfig
from xrtm.forecast.providers.inference.factory import ModelFactory

config = GeminiConfig(model_id="gemini-2.0-flash")
model = ModelFactory.get_provider(config)
```

**After** (provider-free):
```python
from xrtm.product.providers import DeterministicProvider

model = DeterministicProvider()
```

### Cache Inspection

The DeterministicProvider maintains cache statistics:

```python
provider = DeterministicProvider()

# Make some calls
response1 = provider.generate_content("Question 1")
response2 = provider.generate_content("Question 1")  # cache hit
response3 = provider.generate_content("Question 2")  # cache miss

# Inspect cache
snapshot = provider.cache_snapshot
print(f"Hits: {snapshot['hits']}")
print(f"Misses: {snapshot['misses']}")
print(f"Hit rate: {snapshot['hit_rate']:.2%}")
print(f"Entries: {snapshot['entries']}")
```

---

## Testing Best Practices

### Unit Tests

Use the DeterministicProvider for fast, deterministic unit tests:

```python
import pytest
from xrtm.product.providers import DeterministicProvider
from my_agent import MyAgent

@pytest.fixture
def mock_provider():
    return DeterministicProvider()

def test_agent_forecast(mock_provider):
    agent = MyAgent(model=mock_provider)
    result = agent.run("Test question")
    assert result.probability > 0.0
    assert result.probability < 1.0
```

### Integration Tests

Test complete pipelines without API dependencies:

```python
from xrtm.product.providers import DeterministicProvider
from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst

async def test_full_pipeline():
    provider = DeterministicProvider()
    agent = ForecastingAnalyst(model=provider)
    
    result = await agent.run("Will event X happen?")
    
    assert result.confidence is not None
    assert len(result.reasoning) > 0
    assert provider.cache_snapshot["misses"] > 0
```

### CI/CD Pipelines

Provider-free mode enables fast, reliable CI checks:

```yaml
# .github/workflows/test.yml
- name: Run provider-free smoke test
  run: |
    xrtm demo --provider mock --limit 10
    xrtm perf run \
      --scenario provider-free-smoke \
      --iterations 3 \
      --limit 10 \
      --fail-on-budget
```

---

## Comparison: Mock vs Local-LLM

| Feature | `--provider mock` | `--provider local-llm` |
|---------|------------------|------------------------|
| **Setup time** | 0 seconds | 30-60 minutes |
| **Prerequisites** | None | Local server, model weights, GPU |
| **Requires API key** | No | No (but needs local server) |
| **Network calls** | No | Yes (to localhost) |
| **Setup complexity** | None | High (model download, server config) |
| **Deterministic** | Yes | No |
| **Realistic output** | Structured but synthetic | Real LLM reasoning |
| **Speed** | Milliseconds | Seconds (10-90s, depends on hardware) |
| **Cost** | Free | Free (but hardware/electricity costs) |

**When to use mock**:
- ✅ Learning XRTM concepts (recommended starting point)
- ✅ Writing tests
- ✅ CI/CD pipelines
- ✅ Performance benchmarks
- ✅ Rapid iteration without API costs

**When to use local-llm**:
- ⚠️ Testing real LLM behavior locally (after setup)
- ⚠️ Privacy-sensitive deployments
- ⚠️ Offline operation requirements
- ⚠️ Evaluating specific model capabilities

### Local-LLM Prerequisites and Setup

If you choose local-llm mode, follow these steps:

#### 1. Install and Start a Local Inference Server

Common options:
- **llama.cpp**: Lightweight, C++ implementation
- **Ollama**: User-friendly, includes model management
- **LocalAI**: Drop-in OpenAI replacement

Example with llama.cpp server:

```bash
# Download and build llama.cpp (one-time setup)
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Download a model (example: Qwen 7B Q4 quantized, ~4GB)
# Use huggingface-cli or wget to download GGUF files

# Start the server
./llama-server \
  --model path/to/your/model.gguf \
  --port 8080 \
  --ctx-size 4096 \
  --n-gpu-layers 35
```

#### 2. Verify Server Health

```bash
export XRTM_LOCAL_LLM_BASE_URL=http://localhost:8080/v1
xrtm local-llm status
```

**Expected output**:
```
✓ Endpoint: http://localhost:8080/v1
✓ Health check: PASS
✓ Models available: 1
  - Qwen3.5-27B-Q4_K_M.gguf
✓ GPU: NVIDIA GeForce RTX 3090 (8192 MiB used / 24576 MiB total)
```

#### 3. Run Your First Local-LLM Forecast

```bash
xrtm demo --provider local-llm --limit 1 --max-tokens 768
```

**Expected runtime**: 10-90 seconds depending on hardware.

For detailed troubleshooting, see the [Troubleshooting](#troubleshooting-local-llm) section.

---

## Relationship to Lower-Level Testing

### Provider Interface Contract

The DeterministicProvider implements the same `InferenceProvider` interface as production backends:

```python
from xrtm.forecast.providers.inference.base import InferenceProvider

class DeterministicProvider(InferenceProvider):
    def generate_content(self, prompt: Any, **kwargs) -> ModelResponse:
        ...
    
    async def generate_content_async(self, prompt: Any, **kwargs) -> ModelResponse:
        ...
    
    async def stream(self, messages: list[dict[str, str]], **kwargs):
        ...
```

This means:
- Any agent that works with DeterministicProvider will work with real providers
- Tests written with DeterministicProvider validate agent logic, not LLM behavior
- Switching providers requires only configuration changes, not code changes

### Test Doubles vs Mocks

XRTM uses **test doubles** (realistic fakes) rather than traditional mocks:

- **Mock** (unittest.mock): Verifies method calls but doesn't provide real behavior
- **Test Double** (DeterministicProvider): Provides realistic behavior without external dependencies

The DeterministicProvider is a test double because it:
- Returns valid forecast responses
- Maintains state (cache)
- Follows the same async patterns
- Produces outputs that exercise downstream code

### When to Use Mock Libraries

Use traditional mocks (`unittest.mock`, `pytest-mock`) when:
- Testing error handling paths
- Verifying specific method call sequences
- Simulating API failures

Use DeterministicProvider when:
- Testing happy path agent logic
- Running full pipelines
- Benchmarking performance
- Learning XRTM concepts

---

## Example: Provider-Free Analyst

Here's a complete example of using the DeterministicProvider with the ForecastingAnalyst:

```python
"""
Provider-Free Analyst Example
Demonstrates using the DeterministicProvider for testing and learning.
"""

import asyncio
from xrtm.product.providers import DeterministicProvider
from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst


async def main():
    # Create provider-free model
    provider = DeterministicProvider()
    
    # Create agent with provider-free backend
    agent = ForecastingAnalyst(model=provider)
    
    print("--- Provider-Free Forecasting Analyst ---")
    print(f"Model: {provider.model_id}")
    print(f"Base URL: {provider.base_url}")
    print()
    
    # Run forecasts
    questions = [
        "Will the S&P 500 close above 5,000 by end of 2026?",
        "Will inflation exceed 3% in 2026?",
        "Will AGI be announced before 2030?",
    ]
    
    for question in questions:
        result = await agent.run(question)
        print(f"Question: {question}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Reasoning: {result.reasoning[:100]}...")
        print()
    
    # Inspect cache
    cache = provider.cache_snapshot
    print("--- Cache Statistics ---")
    print(f"Hits: {cache['hits']}")
    print(f"Misses: {cache['misses']}")
    print(f"Hit rate: {cache['hit_rate']:.2%}")
    print(f"Entries: {cache['entries']}")


if __name__ == "__main__":
    asyncio.run(main())
```

Save this as `forecast/examples/providers/provider_free_analyst.py` and run:

```bash
python forecast/examples/providers/provider_free_analyst.py
```

---

## Discovering Examples

### CLI Examples

All CLI commands support `--provider mock`:

```bash
# Core workflow
xrtm demo --provider mock --limit 2
xrtm run profile <profile-name>  # if profile uses mock

# Monitoring
xrtm monitor start --provider mock --limit 2

# Performance
xrtm perf run --scenario provider-free-smoke --iterations 3

# Validation
xrtm validate run --provider mock --limit 10
```

### Library Examples

Adapt any example in `forecast/examples/` by replacing the provider configuration:

1. Navigate to an example:
   ```bash
   cd forecast/examples/kit/minimal_agent
   ```

2. Open the script and replace:
   ```python
   # FROM:
   config = GeminiConfig(model_id="gemini-2.0-flash")
   model = ModelFactory.get_provider(config)
   
   # TO:
   from xrtm.product.providers import DeterministicProvider
   model = DeterministicProvider()
   ```

3. Run the modified example:
   ```bash
   python run_minimal_agent.py
   ```

### Hidden Examples

Some examples already use deterministic providers internally for testing:

- `forecast/tests/integration/test_provider_conformance.py`: Provider interface tests
- CLI smoke tests in `xrtm/tests/`: Product shell validation

Explore the test suites for more provider-free patterns.

---

## Troubleshooting

### Mock Provider Issues

#### Import Error: `DeterministicProvider` not found

**Symptom**:
```
ImportError: cannot import name 'DeterministicProvider' from 'xrtm.forecast.providers'
```

**Solution**:
The DeterministicProvider is in the product layer, not the core library:

```python
# WRONG:
from xrtm.forecast.providers import DeterministicProvider

# RIGHT:
from xrtm.product.providers import DeterministicProvider
```

If you're using the `xrtm-forecast` library standalone (without the `xrtm` product shell), you'll need to install the full `xrtm` package:

```bash
pip install xrtm==0.3.0
```

#### Output Doesn't Look Realistic

The DeterministicProvider generates structured but synthetic responses. If you need realistic reasoning:

1. Use `--provider local-llm` with a local model server
2. Use a cloud provider for testing (Gemini, OpenAI)
3. Accept that provider-free mode is for testing logic, not output quality

#### Cache Hit Rate is 0%

If every call is a cache miss, check that:
- You're calling with identical prompts
- The prompt is serializable (no functions or objects)
- You're reusing the same provider instance

#### Performance is Slower Than Expected

Provider-free mode should complete in milliseconds. If it's slow:
- Check if you're accidentally using a real provider
- Verify `--provider mock` is set (CLI) or using `DeterministicProvider` (library)
- Look for unrelated bottlenecks (file I/O, corpus loading)

### Troubleshooting Local-LLM

Common local-llm setup and runtime issues:

#### Health Check Fails: Connection Refused

**Symptom**:
```
✗ Endpoint health check failed
Error: Connection refused
```

**Causes and solutions**:
1. **Server not running**: Start your llama.cpp/Ollama/LocalAI server first
   ```bash
   # Check if server is running
   ps aux | grep llama-server
   ```

2. **Wrong port**: Check server logs for actual port (default: 8080)
   ```bash
   # Test connectivity
   curl http://localhost:8080/health
   ```

3. **Wrong base URL**: Ensure URL ends with `/v1` and matches server config
   ```bash
   export XRTM_LOCAL_LLM_BASE_URL=http://localhost:YOUR_PORT/v1
   xrtm local-llm status
   ```

**Quick diagnostic**:
```bash
# Test basic connectivity
curl http://localhost:8080/health

# Test OpenAI-compatible endpoint
curl http://localhost:8080/v1/models

# Test with XRTM
xrtm local-llm status
```

All three should succeed for local-llm mode to work.

#### Health Check Fails: Timeout

**Symptom**:
```
✗ Endpoint health check failed
Error: timed out
```

**Causes**:
- Server is starting up (wait 10-30 seconds and retry)
- Model loading is slow (large models can take 1-2 minutes to load)
- Server crashed during startup (check server logs)

**Solution**: Check server logs and wait for "HTTP server listening" message.

Example log output to wait for:
```
llama_model_load: total size = 3820.00 MiB
llama server listening at http://localhost:8080
```

#### Forecast Fails: Out of Memory (OOM)

**Symptom**:
```
RuntimeError: CUDA out of memory
```

**Causes and solutions**:
1. **Model too large for GPU**: Use a smaller or more quantized model
   - 7B Q4 models need ~4-6GB VRAM
   - 13B Q4 models need ~8-10GB VRAM
   - 27B Q4 models need ~16-20GB VRAM

2. **Token budget too high**: Reduce `--max-tokens`
   ```bash
   xrtm demo --provider local-llm --limit 1 --max-tokens 512
   ```

3. **Context length exceeds model**: Check model's max context (usually 4096-8192)

**Quick fix**: Restart the server with fewer GPU layers:
```bash
./llama-server --model model.gguf --n-gpu-layers 20  # reduce from 35
```

Check VRAM usage:
```bash
nvidia-smi
```

#### Forecast Runs But Outputs Are Invalid

**Symptom**:
```
ValueError: Expected forecast JSON with 'probability' field
```

**Causes**:
- Model is too small or under-quantized (use Q4 or higher)
- Token budget is too low (forecast reasoning is truncated)
- Model hasn't been fine-tuned for structured output

**Solution**: Increase token budget and use a larger model:
```bash
xrtm demo --provider local-llm --limit 1 --max-tokens 2048
```

**Model size guidance**:
- Minimum: 7B parameters with Q4 quantization
- Recommended: 7B-13B with Q4 or Q5 quantization
- Best quality: 13B+ with Q5 or Q6 quantization

#### Forecast Is Extremely Slow

**Symptom**: Each forecast takes 5+ minutes (expected: 10-90 seconds).

**Causes and solutions**:
1. **GPU not being used**: Server started without `--n-gpu-layers`
   ```bash
   nvidia-smi  # Should show GPU utilization during forecast
   ```
   Fix: Restart server with GPU acceleration enabled:
   ```bash
   ./llama-server --model model.gguf --n-gpu-layers 35
   ```

2. **Model quantization too low**: Q8/F16 models are slower than Q4
   Fix: Use Q4 quantized models for best speed/quality tradeoff

3. **Token budget too high**: More tokens = more generation time
   Fix: Start with `--max-tokens 768`, increase only if needed

**Expected performance** (reference: RTX 3090, Qwen 7B Q4):
- 768 tokens: 10-30 seconds per forecast
- 2048 tokens: 30-90 seconds per forecast

If significantly slower, GPU may not be in use. Check `nvidia-smi` during forecast.

#### Common Environment Variable Issues

**Problem**: Settings not being picked up.

**Check your environment**:
```bash
# Display current settings
echo $XRTM_LOCAL_LLM_BASE_URL
echo $XRTM_LOCAL_LLM_MODEL
echo $XRTM_LOCAL_LLM_API_KEY

# Set if missing
export XRTM_LOCAL_LLM_BASE_URL=http://localhost:8080/v1
export XRTM_LOCAL_LLM_MODEL=your-model.gguf
export XRTM_LOCAL_LLM_API_KEY=test  # Usually "test" for local servers
```

**Common mistakes**:
- URL missing `/v1` suffix
- Port mismatch between server and environment variable
- Environment variable set in one terminal but running command in another

---

## Summary

| Goal | CLI Command | Library Code |
|------|------------|--------------|
| **Learn XRTM** | `xrtm demo --provider mock --limit 2` | `model = DeterministicProvider()` |
| **Test agent logic** | N/A | Use in unit tests with `pytest` |
| **CI pipeline** | `xrtm perf run --scenario provider-free-smoke` | N/A |
| **Rapid iteration** | `xrtm profile create local-mock --provider mock` | Reuse provider instance |
| **Inspect cache** | `xrtm artifacts inspect runs/<run-id>` | `provider.cache_snapshot` |

**Key takeaway**: Provider-free mode lets you explore, test, and learn XRTM without API keys, cloud dependencies, or network calls. It's deterministic, fast, and perfect for CI/CD pipelines.

For production forecasts, switch to a real provider by changing one line of configuration.

---

## Related Documentation

- **[Getting Started Guide](../../xrtm/docs/getting-started.md)**: CLI quickstart with provider-free examples
- **[Operator Runbook](../../xrtm/docs/operator-runbook.md)**: Full CLI reference, monitoring, and performance testing
- **[Examples](../examples/)**: Library examples showing agent topologies and features
- **[Architecture](architecture.md)**: Core concepts and provider abstraction

---

**Ready to test?** Start with `xrtm demo --provider mock --limit 2` at the CLI, or `model = DeterministicProvider()` in your code.
