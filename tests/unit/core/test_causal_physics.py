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

import pytest

from forecast.core.schemas.forecast import CausalEdge, CausalNode, ForecastOutput
from forecast.core.utils.causal import validate_causal_dag
from forecast.kit.eval.intervention import InterventionEngine


def test_causal_dag_validation():
    r"""Verifies that cycle detection works in the causal graph."""
    nodes = [
        CausalNode(node_id="A", event="Event A"),
        CausalNode(node_id="B", event="Event B"),
    ]

    # Valid DAG
    edges_valid = [CausalEdge(source="A", target="B")]
    assert validate_causal_dag(nodes, edges_valid) is True

    # Invalid Cycle: A -> B -> A
    edges_invalid = [
        CausalEdge(source="A", target="B"),
        CausalEdge(source="B", target="A"),
    ]
    with pytest.raises(ValueError, match="Detected cycles"):
        validate_causal_dag(nodes, edges_invalid)


def test_intervention_propagation():
    r"""Verifies that probability changes propagate downstream."""
    nodes = [
        CausalNode(node_id="A", event="A", probability=0.5),
        CausalNode(node_id="B", event="B", probability=0.5),
        CausalNode(node_id="C", event="C", probability=0.5),
    ]
    edges = [
        CausalEdge(source="A", target="B", weight=1.0),
        CausalEdge(source="B", target="C", weight=1.0),
    ]

    output = ForecastOutput(
        question_id="test",
        confidence=0.5,
        reasoning="test",
        logical_trace=nodes,
        logical_edges=edges
    )

    engine = InterventionEngine()

    # Intervene on A: 0.5 -> 1.0 (delta +0.5)
    new_output = engine.apply_intervention(output, "A", 1.0)

    # B and C should increment by 0.5 (capped at 1.0)
    node_b = next(n for n in new_output.logical_trace if n.node_id == "B")
    node_c = next(n for n in new_output.logical_trace if n.node_id == "C")

    assert node_b.probability == 1.0
    assert node_c.probability == 1.0
    assert new_output.confidence == 1.0

    # Intervene on A: 0.5 -> 0.0 (delta -0.5)
    new_output_2 = engine.apply_intervention(output, "A", 0.0)
    node_b2 = next(n for n in new_output_2.logical_trace if n.node_id == "B")
    node_c2 = next(n for n in new_output_2.logical_trace if n.node_id == "C")

    assert node_b2.probability == 0.0
    assert node_c2.probability == 0.0
    assert new_output_2.confidence == 0.0
