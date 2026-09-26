# Sentinel Protocol: Dynamic Forecasting

The Sentinel protocol captures the *evolution* of a probability over time
rather than a single snapshot.

> **Changed in 0.9–0.10.** The `PollingDriver` background loop was removed.
> Run repeated forecasts with `forecast_many` (see [Policies](policies.md)) or
> scheduled executions, and persist each `ForecastOutput` to build a trajectory.

## Schemas

### ForecastTrajectory
::: xrtm.forecast.core.schemas.forecast.ForecastTrajectory
    rendering:
      show_root_heading: true

### TimeSeriesPoint
::: xrtm.forecast.core.schemas.forecast.TimeSeriesPoint
    rendering:
      show_root_heading: true
