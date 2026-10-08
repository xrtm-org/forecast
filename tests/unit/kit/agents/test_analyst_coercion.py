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

r"""Fallback payload coercion: malformed values must degrade, not crash."""

from xrtm.forecast.kit.agents.specialists.analyst import (
    _coerce_confidence_interval,
    _coerce_probability,
    _safe_causal_edges,
    _safe_causal_nodes,
)


def test_probability_is_clamped_and_coerced():
    assert _coerce_probability(1.5) == 1.0
    assert _coerce_probability(-0.5) == 0.0
    assert _coerce_probability("bad") == 0.5
    assert _coerce_probability(None) == 0.5


def test_interval_is_validated_and_synthesized():
    assert _coerce_confidence_interval({"low": 0.2, "high": 0.8, "level": 0.9}, 0.5) == {
        "low": 0.2,
        "high": 0.8,
        "level": 0.9,
    }
    synthesized = _coerce_confidence_interval({"low": "x"}, 0.5)
    assert synthesized["low"] < 0.5 < synthesized["high"]
    # an interval that does not contain the probability is replaced
    replaced = _coerce_confidence_interval({"low": 0.8, "high": 0.9}, 0.5)
    assert replaced["low"] < 0.5 < replaced["high"]


def test_malformed_nodes_and_edges_are_skipped():
    nodes = _safe_causal_nodes([{"event": "e", "node_id": "n1"}, {"bad": True}])
    assert len(nodes) == 1
    edges = _safe_causal_edges([{"source": "n1", "target": "n1", "weight": 5.0}, {"bad": True}])
    assert len(edges) == 1
    assert edges[0].weight == 1.0  # clamped by _sanitize_edge
