# Topologies API

Topologies are reusable execution-graph patterns that define how multiple agents or tools interact during a run.

A topology is not the forecast reasoning graph. It is the assembly template that wires stages in the execution graph.

## Recursive Consensus

The `RecursiveConsensus` topology implements a peer-review loop where multiple agents must reach a specific threshold of agreement before a forecast is finalized.

::: forecast.kit.topologies.consensus.RecursiveConsensus
    options:
      show_root_heading: true
      show_source: true
