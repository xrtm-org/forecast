# Causal Interpretability API

The Causal Interpretability layer moves the platform from "Black Box" reasoning to explicit Directed Acyclic Graph (DAG) explanations.

## Core: Schemas

### CausalEdge
Represents a directed dependency between two nodes in a reasoning graph.

::: forecast.core.schemas.forecast.CausalEdge
    options:
      show_root_heading: true
      show_source: true

### ForecastOutput.to_networkx
Exports the logical trace as a `networkx.DiGraph` for graph analysis.

---

## Core: Utilities

### validate_causal_dag
Verifies that a reasoning graph is a valid DAG (acyclic).

::: forecast.core.utils.causal.validate_causal_dag
    options:
      show_root_heading: true
      show_source: true

### get_downstream_impact
Identifies all nodes affected by a change to a starting node.

::: forecast.core.utils.causal.get_downstream_impact
    options:
      show_root_heading: true
      show_source: true

---

## Kit: Interventions

### InterventionEngine
Performs "What-If" simulations via do-calculus.

::: forecast.kit.eval.intervention.InterventionEngine
    options:
      show_root_heading: true
      show_source: true
