# coding=utf-8
# Copyright 2026 XRTM Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""
Causal utility functions for DAG validation and graph-theoretic analysis.
"""

from typing import List

import networkx as nx

from xrtm.forecast.core.schemas.forecast import CausalEdge, CausalNode


def validate_causal_dag(nodes: List[CausalNode], edges: List[CausalEdge]) -> bool:
    r"""
    Validates that a set of nodes and edges form a valid Directed Acyclic Graph (DAG).

    Args:
        nodes (`List[CausalNode]`):
            The list of causal nodes (reasoning steps).
        edges (`List[CausalEdge]`):
            The list of causal dependencies.

    Returns:
        `bool`: True if the graph is a valid DAG.

    Raises:
        `ValueError`: If a cycle is detected or if nodes are missing IDs.
    """
    dg = nx.DiGraph()
    for node in nodes:
        dg.add_node(node.node_id)

    for edge in edges:
        dg.add_edge(edge.source, edge.target)

    if not nx.is_directed_acyclic_graph(dg):
        cycles = list(nx.simple_cycles(dg))
        raise ValueError(f"Causal graph is not a DAG. Detected cycles: {cycles}")

    return True


def get_downstream_impact(nodes: List[CausalNode], edges: List[CausalEdge], start_node_id: str) -> List[str]:
    r"""
    Returns a list of all node IDs affected by a change in the starting node.

    Args:
        nodes (`List[CausalNode]`): The trace nodes.
        edges (`List[CausalEdge]`): The trace edges.
        start_node_id (`str`): The ID of the node being modified.

    Returns:
        `List[str]`: List of all downstream node IDs.
    """
    dg = nx.DiGraph()
    dg.add_nodes_from([n.node_id for n in nodes])
    dg.add_edges_from([(e.source, e.target) for e in edges])

    return list(nx.descendants(dg, start_node_id))


__all__ = ["validate_causal_dag", "get_downstream_impact"]
