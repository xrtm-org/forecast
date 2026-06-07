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

r"""Tests for debate and fanout graph patterns."""

from typing import Any
from unittest.mock import MagicMock

from xrtm.forecast.kit.agents.llm import LLMAgent
from xrtm.forecast.kit.patterns import create_debate_graph, create_fanout_graph


class MockLLMAgent(LLMAgent):
    """Minimal LLMAgent for topology testing."""

    def __init__(self, name: str = "test-agent"):
        mock_provider = MagicMock()
        mock_provider.model_id = "mock"
        super().__init__(model=mock_provider, name=name)

    async def run(self, input_data: Any, **kwargs: Any) -> dict[str, Any]:
        return {"result": f"mock-output-from-{self.name}", "probability": 0.5}


def test_create_debate_graph_returns_graph_agent():
    """create_debate_graph should return a GraphAgent."""
    pro = MockLLMAgent("pro-agent")
    con = MockLLMAgent("con-agent")
    judge = MockLLMAgent("judge-agent")

    graph = create_debate_graph(pro, con, judge, max_rounds=2)
    assert graph is not None
    assert graph.name == "DebateGraph"


def test_create_debate_graph_orchestrator_has_correct_nodes():
    """Debate graph orchestrator should register Pro, Con, and Judge nodes."""
    pro = MockLLMAgent("pro-agent")
    con = MockLLMAgent("con-agent")
    judge = MockLLMAgent("judge-agent")

    graph = create_debate_graph(pro, con, judge, max_rounds=2)
    node_names = set(graph.orchestrator.nodes.keys())
    assert "pro-agent" in node_names
    assert "con-agent" in node_names
    assert "judge-agent" in node_names


def test_create_debate_graph_custom_name():
    """Debate graph should accept a custom name."""
    pro = MockLLMAgent("pro")
    con = MockLLMAgent("con")
    judge = MockLLMAgent("judge")

    graph = create_debate_graph(pro, con, judge, name="CustomDebate")
    assert graph.name == "CustomDebate"


def test_create_fanout_graph_returns_graph_agent():
    """create_fanout_graph should return a GraphAgent."""
    workers = [MockLLMAgent(f"worker-{i}") for i in range(3)]
    aggregator = MockLLMAgent("aggregator")

    graph = create_fanout_graph(workers, aggregator)
    assert graph is not None
    assert graph.name == "FanOutGraph"


def test_create_fanout_graph_registers_all_workers():
    """Fanout graph should register all worker nodes plus aggregator."""
    workers = [MockLLMAgent(f"worker-{i}") for i in range(3)]
    aggregator = MockLLMAgent("aggregator")

    graph = create_fanout_graph(workers, aggregator)
    node_names = set(graph.orchestrator.nodes.keys())
    for i in range(3):
        assert f"worker-{i}" in node_names
    assert "aggregator" in node_names


def test_create_fanout_graph_custom_name():
    """Fanout graph should accept a custom name."""
    workers = [MockLLMAgent("w1")]
    aggregator = MockLLMAgent("agg")

    graph = create_fanout_graph(workers, aggregator, name="CustomFanOut")
    assert graph.name == "CustomFanOut"
