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

r"""Tests for RecursiveConsensus topology."""

from typing import Any

import pytest

from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.kit.topologies.consensus import RecursiveConsensus


def _mock_analyst(probability: float = 0.7, name: str = "analyst"):
    """Create a mock analyst wrapper callable."""

    async def wrapper(state: BaseGraphState, reporter: Any) -> dict[str, Any]:
        return {
            "analyst": name,
            "probability": probability,
            "reasoning": f"Mock reasoning from {name}",
        }
    return wrapper


def _mock_supervisor(decision: str = "APPROVE"):
    """Create a mock supervisor callable."""
    async def wrapper(state: BaseGraphState) -> str:
        return decision
    return wrapper


def _mock_aggregator(result: float = 0.72):
    """Create a mock aggregator callable."""
    async def wrapper(state: BaseGraphState) -> dict[str, Any]:
        return {"aggregated_probability": result, "method": "mock-mean"}
    return wrapper


def _mock_red_team(challenge: str = "No counter-arguments found."):
    """Create a mock red team wrapper."""
    async def wrapper(state: BaseGraphState) -> dict[str, Any]:
        return {"red_team_finding": challenge}
    return wrapper


def test_recursive_consensus_builds_orchestrator():
    """RecursiveConsensus should build an orchestrator with registered nodes."""
    consensus = RecursiveConsensus(
        analyst_wrappers=[_mock_analyst(0.6), _mock_analyst(0.8)],
        supervisor_wrapper=_mock_supervisor("APPROVE"),
        aggregator_wrapper=_mock_aggregator(0.7),
        max_cycles=2,
    )
    orch = consensus.build_graph()
    assert orch is not None
    assert len(orch.nodes) > 0


def test_recursive_consensus_with_red_team():
    """RecursiveConsensus should accept an optional red team wrapper."""
    consensus = RecursiveConsensus(
        analyst_wrappers=[_mock_analyst(0.5)],
        supervisor_wrapper=_mock_supervisor("APPROVE"),
        aggregator_wrapper=_mock_aggregator(0.5),
        red_team_wrapper=_mock_red_team(),
        max_cycles=1,
    )
    orch = consensus.build_graph()
    assert orch is not None


def test_recursive_consensus_with_ivw():
    """RecursiveConsensus should support IVW aggregation with use_ivw=True."""
    consensus = RecursiveConsensus(
        analyst_wrappers=[_mock_analyst(0.4), _mock_analyst(0.6), _mock_analyst(0.8)],
        supervisor_wrapper=_mock_supervisor("APPROVE"),
        use_ivw=True,
        max_cycles=1,
    )
    orch = consensus.build_graph()
    assert orch is not None
    assert len(orch.nodes) > 0


def test_recursive_consensus_requires_aggregator_or_ivw():
    """RecursiveConsensus should raise if neither aggregator nor use_ivw is set."""
    with pytest.raises(ValueError, match="aggregator_wrapper"):
        RecursiveConsensus(
            analyst_wrappers=[_mock_analyst(0.5)],
            supervisor_wrapper=_mock_supervisor("APPROVE"),
            use_ivw=False,
        )


def test_recursive_consensus_max_cycles_configures_orchestrator():
    """max_cycles parameter should affect orchestrator configuration."""
    c1 = RecursiveConsensus(
        analyst_wrappers=[_mock_analyst(0.5)],
        supervisor_wrapper=_mock_supervisor("APPROVE"),
        aggregator_wrapper=_mock_aggregator(0.5),
        max_cycles=1,
    )
    c2 = RecursiveConsensus(
        analyst_wrappers=[_mock_analyst(0.5)],
        supervisor_wrapper=_mock_supervisor("APPROVE"),
        aggregator_wrapper=_mock_aggregator(0.5),
        max_cycles=5,
    )
    orch1 = c1.build_graph()
    orch2 = c2.build_graph()
    # Different max_cycles should produce different orchestrator max visit counts
    assert orch1.max_cycles != orch2.max_cycles
