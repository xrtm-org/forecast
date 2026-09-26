# Causal Interpretability API

The causal layer moves the platform from black-box outputs to explicit
reasoning-graph explanations. It describes the logical structure inside a
forecast result, separate from the runtime execution graph.

## Schemas

### CausalEdge
Represents a directed dependency between two nodes in a reasoning graph
(negative weights are inhibitory).

::: xrtm.data.core.schemas.forecast.CausalEdge
    options:
      show_root_heading: true
      show_source: true

`ForecastOutput.to_networkx()` exports the reasoning graph as a `networkx.DiGraph`
for downstream analysis.

## Validation

### validate_causal_graph
Verifies that a reasoning graph is structurally valid (known edge endpoints,
acyclic).

::: xrtm.forecast.core.utils.graph_validation.validate_causal_graph
    options:
      show_root_heading: true
      show_source: true

The analyst records issues in `metadata.raw_data["graph_issues"]` and raises
`GraphError` when constructed with `strict_dag=True`.
