# Async Runtime API

The `AsyncRuntime` is the institutional abstraction for all `asyncio` operations in `xrtm-forecast`. It ensures high performance, temporal integrity, and auditability across the reasoning graph.

## Rationale

- **Temporal Integrity**: standard `asyncio.sleep` cannot be intercepted. `AsyncRuntime.sleep` is point-in-time aware for backtesting.
- **Structured Concurrency**: centralizing task spawning via TaskGroups prevents background task leakage.
- **Performance**: transparently installs `uvloop` if available.
- **Auditability**: provides hooks for OpenTelemetry (OTel) trace propagation.

## Reference

::: forecast.core.runtime.AsyncRuntime
    options:
      show_root_heading: true
      show_source: true
      members:
        - run_main
        - task_group
        - spawn
        - sleep
