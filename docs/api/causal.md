# Causal Interpretability API

The causal interpretability layer moves the platform from black-box outputs to explicit reasoning-graph explanations.

This API describes the logical or causal structure inside a forecast result. It is separate from the runtime execution graph managed by the orchestrator.

## Core: Schemas

### CausalEdge
Represents a directed dependency between two nodes in a reasoning graph.

::: forecast.core.schemas.forecast.CausalEdge
    options:
      show_root_heading: true
      show_source: true

### ForecastOutput.to_networkx
Exports the reasoning graph as a `networkx.DiGraph` for downstream analysis.

---

## Core: Utilities

### validate_causal_dag
Verifies that a reasoning graph is a valid DAG (acyclic).

::: forecast.core.utils.causal.validate_causal_dag
    options:
      show_root_heading: true
      show_source: true

### get_downstream_impact
Identifies all reasoning-graph nodes affected by a change to a starting node.

::: forecast.core.utils.causal.get_downstream_impact
    options:
      show_root_heading: true
      show_source: true

---

## Kit: Interventions

### InterventionEngine
Performs what-if simulations via do-calculus.

::: forecast.kit.eval.intervention.InterventionEngine
    options:
      show_root_heading: true
      show_source: true
