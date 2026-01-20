# Temporal Integrity (Chronos Protocol)

The **Chronos Protocol** ensures that forecasting agents cannot "cheat" by accessing information from the future. This is critical for valid backtesting and scientific reproducibility.

## The Problem: The Profit Mirage

When backtesting forecasting strategies, a hidden danger lurks: **semantic leakage**.

```
You build a strategy that trades the 2022 Tech Crash.
Your agent shorts NVIDIA perfectly. Why?

Because the LLM was trained in 2023 and *knows* NVIDIA crashed.
This is not reasoning—it's recitation.
```

Standard backtesting frameworks prevent *data* leakage (looking at tomorrow's price), but they cannot prevent *semantic* leakage where the model's parametric knowledge contains future outcomes.

## The Solution: Time-Travel Guardian

`xrtm-forecast` implements a multi-layer temporal integrity system:

### 1. TemporalContext

Every reasoning session operates within a frozen time context:

```python
from forecast.core.schemas.graph import BaseGraphState

# Create a state anchored to a specific point in time
state = BaseGraphState(
    subject_id="tech_crash_2022",
    context={"sim_time": datetime(2022, 1, 15)}
)
```

### 2. The Guardian Interceptor

The `Guardian` wraps all external I/O (search, news, data feeds) and validates timestamps:

```python
from forecast.core.stages.guardian import Guardian

# Guardian intercepts search results
# If any result has timestamp > sim_time, it raises TemporalViolation
guardian = Guardian(sim_time=datetime(2022, 1, 15))
validated_results = guardian.filter_results(raw_search_results)
```

### 3. Chronos-Sleep Integration

The `AsyncRuntime.sleep()` function is linked to `TemporalContext`:

```python
from forecast.core.runtime import AsyncRuntime

# In backtest mode, this doesn't actually wait—it fast-forwards
# the simulated clock, enabling 1000x speedup
await AsyncRuntime.sleep(3600)  # "Waits" 1 hour in sim time
```

## Trade-offs

| Aspect | Behavior |
| :--- | :--- |
| **Default Mode** | Metadata-based filtering (fast, but relies on source accuracy) |
| **Gold Standard Mode** | Wayback Machine verification (slow, but zero leakage) |

## Related Concepts

- [Orchestration](orchestration.md) — How the Guardian integrates with graph execution
- [Calibration](calibration.md) — Why temporal integrity matters for accuracy metrics
