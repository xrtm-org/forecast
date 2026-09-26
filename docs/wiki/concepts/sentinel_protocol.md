# The Sentinel Protocol

## Overview

Traditional forecasting engines produce a **static snapshot** — a single
probability at one moment in time. Real-world events evolve continuously.

The **Sentinel Protocol** provides the architecture for **Dynamic Forecasting**:
tracking how a forecast's confidence changes as new information arrives.

## Core Concepts

### Trajectories vs Snapshots

| Static Forecasting | Dynamic Forecasting |
|--------------------|---------------------|
| Single probability P(t) | Time-series [P(t₁), P(t₂), ...] |
| Run once, done | Continuous updates |
| Expensive re-runs | Delta updates (small evidence prompts) |

### The Delta Function

Instead of re-running the full research execution graph for every update, a
dynamic forecaster can update on deltas:

1. Provide: `previous_reasoning + new_evidence`
2. Receive: `updated_confidence + reasoning_delta`
3. Cost: a fraction of a full research re-run

## Producing Trajectories in 0.10

> **Changed in 0.9–0.10.** The bundled `PollingDriver` / `StreamDriver` /
> `ProcessSentinel` drivers were removed from the engine. Build trajectories
> from repeated forecasts instead:

```python
from xrtm.forecast.kit.batch import forecast_many

# Run a batch now, persist each ForecastOutput, and repeat on your schedule
result = await forecast_many(analyst, questions, concurrency=5, ledger=ledger)
for output in result.outputs:
    store(output)  # your trajectory storage
```

Off-peak scheduling and cost accounting for those runs are engine policies —
see [Policies](../api/policies.md).

## Schemas

`ForecastTrajectory` and `TimeSeriesPoint` (see the
[Sentinel API reference](../api/sentinel.md)) provide the storage shape for a
probability series; the analyst's `provenance` and `usage` fields make each
point auditable.
