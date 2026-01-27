# XRTM Governance: The Layer Hierarchy

This document defines the strict dependency hierarchy for the XRTM ecosystem. Violating these rules will cause circular import errors and break CI.

## The Four Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: xrtm-train (Optimization Loop)                        │
│  ↳ Can import from: forecast, eval, data                        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: xrtm-forecast (Reasoning Engine)                      │
│  ↳ Can import from: eval, data                                  │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: xrtm-eval (Scoring & Trust)                           │
│  ↳ Can import from: data                                        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: xrtm-data (Foundation Schemas)                        │
│  ↳ Can import from: (nothing - zero dependencies)               │
└─────────────────────────────────────────────────────────────────┘
```

## Import Rules

| Package | CAN import from | CANNOT import from |
|---------|-----------------|-------------------|
| `xrtm-data` | *(none)* | eval, forecast, train |
| `xrtm-eval` | data | forecast, train |
| `xrtm-forecast` | data, eval | train |
| `xrtm-train` | data, eval, forecast | *(none)* |

## What Belongs Where

### xrtm-data (Layer 1)
- Pydantic schemas for forecasts, questions, resolutions
- `ForecastOutput`, `ForecastQuestion`, `CausalNode`, `CausalEdge`
- `MetadataBase` with temporal snapshots

### xrtm-eval (Layer 2)
- Scoring metrics (`BrierScoreEvaluator`, `ExpectedCalibrationErrorEvaluator`)
- Trust primitives (`IntegrityGuardian`, `SourceTrustRegistry`)
- Intervention and analysis (`InterventionEngine`, `SliceAnalytics`)

### xrtm-forecast (Layer 3)
- Graph orchestration (`Orchestrator`, `BaseGraphState`)
- Agent abstractions (`Agent`, `LLMAgent`, `ToolAgent`, `GraphAgent`)
- Inference providers (`OpenAIProvider`, `GeminiProvider`, etc.)
- Agent topologies (`RecursiveConsensus`, `DebateTopology`)

### xrtm-train (Layer 4)
- Backtesting (`Backtester`, `BacktestRunner`, `BacktestDataset`)
- Trace replay (`TraceReplayer`)
- Calibration optimization

## Detecting Violations

If you see an error like:
```
ImportError: cannot import name 'X' from 'xrtm.forecast' 
```

Check:
1. Is `X` in a higher layer than the importing module?
2. Does the import create a circular dependency?

Use `uv run ruff check .` and `uv run mypy .` to catch violations early.

## Historical Violations Fixed in v0.6.0

1. **`epistemics.py`**: Moved from `forecast/core/` to `eval/core/` because it had no forecast dependencies.
2. **`AnalystWorkbench`**: Moved from `eval/kit/` to `forecast/kit/` because it uses `Orchestrator`.
3. **`SovereigntyVerifier`**: Moved to `forecast/core/` because it uses `BaseGraphState`.
