# Centaur Protocol API (Human-in-the-Loop)

The Centaur Protocol provides the interface for integrating human domain expertise into the agentic reasoning loop.

## Core: Interfaces

### HumanProvider
The abstract base class for human intervention sources (CLI, Web UI, API).

::: forecast.core.interfaces.HumanProvider
    options:
      show_root_heading: true
      show_source: true

---

## Kit: Workbench & Evaluation

### AnalystWorkbench
A topology for human-AI collaborative forecasting.

::: forecast.kit.eval.workbench.AnalystWorkbench
    options:
      show_root_heading: true
      show_source: true

### BiasInterceptor
An evaluator that audits reasoning for cognitive biases.

::: forecast.kit.eval.bias.BiasInterceptor
    options:
      show_root_heading: true
      show_source: true
