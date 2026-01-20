# Sentinel Protocol API

The Sentinel module provides infrastructure for **Dynamic Forecasting** — tracking
how a forecast's confidence evolves as new information becomes available.

## Core Classes

### `SentinelDriver` (Abstract Base)
The interface that all Sentinel implementations must follow.

```python
from forecast.kit.sentinel import SentinelDriver

class MySentinel(SentinelDriver):
    async def register_watch(self, question, rules): ...
    async def unregister_watch(self, question_id): ...
    async def get_trajectory(self, question_id): ...
```

### `PollingDriver`
A zero-infrastructure implementation that periodically checks for updates.

```python
from forecast.kit.sentinel import PollingDriver

driver = PollingDriver(model=llm, poll_interval=3600)
await driver.register_watch(question, rules)
await driver.run(max_cycles=10)
```

### `TriggerRules`
Configuration for when to update a forecast.

| Field | Type | Description |
|-------|------|-------------|
| `interval_seconds` | `int` | Minimum time between updates |
| `max_updates` | `int` | Maximum updates before stopping |

## Schema: `ForecastTrajectory`
Defined in `forecast.core.schemas.forecast`, this schema stores the time-series
of probability updates for a single question.

```python
from forecast.core.schemas.forecast import ForecastTrajectory

trajectory = ForecastTrajectory(
    question_id="q123",
    points=[TimeSeriesPoint(timestamp=now, value=0.75)],
    final_confidence=0.75
)
```
