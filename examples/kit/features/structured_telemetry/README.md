# Structured Telemetry

**Script**: `run_structured_telemetry.py`

Shows how to emit structured JSON logs from the reasoning engine. This is crucial for production observability, allowing you to ingest traces into tools like Datadog, LangSmith, or honeycomb.io.

## Usage

```bash
# From repository root
python3 examples/kit/features/structured_telemetry/run_structured_telemetry.py
```

## Concepts
- **Structured Logging**: Logs as data (JSON), not strings.
- **Trace IDs**: correlating events across a distributed system.
