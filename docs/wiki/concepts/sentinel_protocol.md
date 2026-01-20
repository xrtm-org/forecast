# The Sentinel Protocol

## Overview

Traditional forecasting engines produce a **static snapshot** — a single probability
at one moment in time. But real-world events evolve continuously.

The **Sentinel Protocol** provides the architecture for **Dynamic Forecasting**:
tracking how a forecast's confidence changes as new information arrives.

## Core Concepts

### Trajectories vs Snapshots
| Static Forecasting | Dynamic Forecasting |
|--------------------|---------------------|
| Single probability P(t) | Time-series [P(t₁), P(t₂), ...] |
| Run once, done | Continuous updates |
| Expensive re-runs | Delta updates (~500 tokens) |

### The Delta Function
Instead of re-running the full research graph for every update, we use
**Bayesian Updating**:

1. Agent receives: `previous_reasoning + new_evidence`
2. Agent outputs: `updated_confidence + reasoning_delta`
3. Cost: ~500 tokens (vs. 10,000+ for full re-run)

## Drivers

The Sentinel Protocol uses a **Driver** abstraction for flexibility:

| Driver | Latency | Complexity | Use Case |
|--------|---------|------------|----------|
| `PollingDriver` | Minutes | Zero infra | Research, laptops |
| `StreamDriver` | Seconds | Redis/Kafka | Enterprise scale |
| `ProcessSentinel` | Sub-second | Complex | Crisis monitoring |

## Example

```python
from forecast.kit.sentinel import PollingDriver, TriggerRules

driver = PollingDriver(model=llm, poll_interval=3600)
await driver.register_watch(
    question,
    TriggerRules(interval_seconds=3600, max_updates=24)
)

# Run for 24 hours
await driver.run(max_cycles=24)

trajectory = await driver.get_trajectory(question.id)
print(f"Final confidence: {trajectory.final_confidence}")
```
