# Memory API

> **Changed in 0.9–0.10.** The unified semantic/vector memory stack was removed;
> the supported memory primitive is the fact store.

::: xrtm.forecast.core.memory.graph.FactStore
    options:
      show_root_heading: true

::: xrtm.forecast.core.memory.graph.Fact
    options:
      show_root_heading: true

Agents can attach a fact store via `agent.set_fact_store(...)`; see the
architecture guide for the "institutional memory" pattern.
