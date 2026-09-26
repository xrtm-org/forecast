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

r"""Tests for causal-graph validation."""

from xrtm.data.core.schemas.forecast import CausalEdge, CausalNode

from xrtm.forecast.core.utils.graph_validation import validate_causal_graph


def test_valid_graph_has_no_issues():
    nodes = [CausalNode(node_id="n1", event="A"), CausalNode(node_id="n2", event="B")]
    edges = [CausalEdge(source="n1", target="n2", weight=-0.4)]
    assert validate_causal_graph(nodes, edges) == []


def test_unknown_edge_endpoints_are_reported():
    nodes = [CausalNode(node_id="n1", event="A")]
    edges = [CausalEdge(source="n1", target="n9")]
    issues = validate_causal_graph(nodes, edges)
    assert any("n9" in issue for issue in issues)


def test_cycles_are_reported():
    nodes = [CausalNode(node_id="n1", event="A"), CausalNode(node_id="n2", event="B")]
    edges = [
        CausalEdge(source="n1", target="n2"),
        CausalEdge(source="n2", target="n1"),
    ]
    issues = validate_causal_graph(nodes, edges)
    assert any("cycle" in issue for issue in issues)


def test_empty_graph_is_valid():
    assert validate_causal_graph([], []) == []
