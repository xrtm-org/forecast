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

r"""Causal-graph validation utilities.

Forecast outputs carry a causal graph (nodes + directed edges). LLMs
occasionally emit edges that reference unknown nodes or even cycles; these
helpers surface those issues so callers can flag or reject them.

Example:
    >>> from xrtm.forecast.core.utils.graph_validation import validate_causal_graph
    >>> validate_causal_graph(nodes=[], edges=[])
    []
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

__all__ = ["validate_causal_graph"]


def validate_causal_graph(nodes: Sequence[Any], edges: Sequence[Any]) -> List[str]:
    r"""Return a list of structural issues in a causal graph.

    Checks that every edge endpoint refers to a known node and that the graph
    is acyclic. An empty list means the graph is structurally valid.

    Args:
        nodes: Objects with a ``node_id`` attribute (e.g. ``CausalNode``).
        edges: Objects with ``source``/``target`` attributes (e.g. ``CausalEdge``).

    Returns:
        Human-readable issue strings (empty when valid).
    """
    issues: List[str] = []

    node_ids = {str(getattr(node, "node_id", "")) for node in nodes}
    node_ids.discard("")

    adjacency: Dict[str, List[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        source = getattr(edge, "source", None)
        target = getattr(edge, "target", None)
        if source not in node_ids:
            issues.append(f"edge source {source!r} is not a known node")
        if target not in node_ids:
            issues.append(f"edge target {target!r} is not a known node")
        if source in node_ids and target in node_ids:
            adjacency[source].append(target)

    if _has_cycle(adjacency):
        issues.append("causal graph contains a cycle")

    return issues


def _has_cycle(adjacency: Dict[str, List[str]]) -> bool:
    r"""Iterative DFS cycle detection over a directed adjacency map."""
    white, gray, black = 0, 1, 2
    color: Dict[str, int] = {node_id: white for node_id in adjacency}

    for start in adjacency:
        if color[start] != white:
            continue
        color[start] = gray
        stack = [(start, iter(adjacency[start]))]
        while stack:
            node, neighbours = stack[-1]
            try:
                neighbour = next(neighbours)
            except StopIteration:
                color[node] = black
                stack.pop()
                continue
            if color.get(neighbour) == gray:
                return True
            if color.get(neighbour) == white:
                color[neighbour] = gray
                stack.append((neighbour, iter(adjacency[neighbour])))
    return False
