# Sentinel Protocol: Dynamic Forecasting

The `sentinel` module provides the drivers and orchestration logic for **Dynamic Forecasting**—the ability for agents to continuously monitor news feeds and emit probability updates over time.

## Polling Driver

The `PollingDriver` is the primary high-level interface for running background forecasting loops.

### PollingDriver
::: forecast.kit.sentinel.polling.PollingDriver
    rendering:
      show_root_heading: true
      show_source: true

## Schemas

### ForecastTrajectory
::: forecast.core.schemas.forecast.ForecastTrajectory
    rendering:
      show_root_heading: true

### TimeSeriesPoint
::: forecast.core.schemas.forecast.TimeSeriesPoint
    rendering:
      show_root_heading: true
