# Minimal Agent

**Script**: `run_minimal_agent.py`

The smallest forecasting-agent example in `xrtm-forecast`. The script configures a model explicitly, creates a `ForecastingAnalyst`, and runs one direct forecast request without extra tools or orchestration.

## Usage

```bash
# From repository root
python3 examples/kit/minimal_agent/run_minimal_agent.py
```

## Concepts
- **ForecastingAnalyst**: the specialist agent used by the script.
- **InferenceProvider**: connecting the agent to a model backend.
- **Direct Interaction**: sending one forecasting prompt and inspecting the returned probability and reasoning.
