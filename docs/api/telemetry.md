# Telemetry

> **Moved in 0.9–0.10.** `TelemetryManager`, `TelemetrySpan`, and `Audit` were
> removed; telemetry is now part of the forecast contract.

Every `ForecastOutput` carries typed telemetry (xrtm-data 0.4.0+), mirrored in
governance Forecast Object v1.2 under `metadata.telemetry`:

- `usage` — prompt / completion / cached / reasoning / total tokens
- `provenance` — provider, model, prompt id, temperature, thinking mode, cache hit
- `parse_status` — `ok` | `empty_content` | `invalid_json` | `schema_error`

::: xrtm.data.core.schemas.forecast.TokenUsage
    options:
      show_root_heading: true

::: xrtm.data.core.schemas.forecast.ForecastProvenance
    options:
      show_root_heading: true

Cost accounting builds on `usage` — see [Policies](policies.md).
