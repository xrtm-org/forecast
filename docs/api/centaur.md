# Centaur Protocol API (Human-in-the-Loop)

The Centaur Protocol provides the interface for integrating human domain
expertise into the agentic reasoning loop.

## Core: Interfaces

### HumanProvider
The abstract base class for human intervention sources (CLI, Web UI, API).

::: xrtm.forecast.core.interfaces.HumanProvider
    options:
      show_root_heading: true
      show_source: true

---

> **Changed in 0.9–0.10.** The `AnalystWorkbench` helper and the
> `BiasInterceptor` auditor were removed. Wire a `HumanProvider` into
> `state.context["human_provider"]` and add `human:` nodes to the
> orchestrator graph — see
> [Human-in-the-Loop](../wiki/concepts/human_loop.md).
