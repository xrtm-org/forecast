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

from datetime import datetime
from typing import Callable, Optional

import pytest

from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.forecast import ForecastQuestion, ForecastResolution
from forecast.core.schemas.graph import BaseGraphState
from forecast.kit.eval.runner import BacktestDataset, BacktestInstance, BacktestRunner


# 1. Simple mock node that returns a confidence score based on the input
async def predictor_node(state: BaseGraphState, on_progress: Optional[Callable] = None):
    r"""A mock predictor node that returns confidence based on query keywords."""
    # Just echo a value or simple logic
    query = state.node_reports.get("ingestion", "0.5")
    try:
        # Mock logic: if the query contains 'high', confidence is 0.9, else 0.1
        conf = 0.9 if "high" in query.lower() else 0.1
        state.node_reports["predictor"] = {"confidence": conf}
    except Exception:
        state.node_reports["predictor"] = {"confidence": 0.5}
    return None  # End of graph


@pytest.fixture
def mock_orchestrator():
    orch = Orchestrator()

    async def ingestion_node(s, p):
        return "predictor"

    orch.add_node("ingestion", ingestion_node)
    orch.add_node("predictor", predictor_node)
    orch.add_edge("ingestion", "predictor")
    orch.set_entry_point("ingestion")
    return orch


@pytest.mark.asyncio
async def test_backtest_runner_brier_calculation(mock_orchestrator):
    r"""Verifies the BacktestRunner correctly calculates Brier Scores across a dataset."""
    runner = BacktestRunner(mock_orchestrator, concurrency=2)

    # Create dataset:
    # 1. 'high' -> predicted 0.9, actual 1.0 (True) -> BS = (0.9-1.0)^2 = 0.01
    # 2. 'low' -> predicted 0.1, actual 0.0 (False) -> BS = (0.1-0.0)^2 = 0.01
    # Mean BS should be 0.01

    dataset = BacktestDataset(
        name="synthetic_test",
        items=[
            BacktestInstance(
                question=ForecastQuestion(id="q1", title="high probability event"),
                resolution=ForecastResolution(question_id="q1", outcome="1"),
                reference_time=datetime(2024, 1, 1),
            ),
            BacktestInstance(
                question=ForecastQuestion(id="q2", title="low probability event"),
                resolution=ForecastResolution(question_id="q2", outcome="0"),
                reference_time=datetime(2024, 1, 1),
            ),
        ],
    )

    report = await runner.run(dataset)

    assert report.total_evaluations == 2
    assert report.mean_score == pytest.approx(0.01)
    assert report.results[0].score == pytest.approx(0.01)
    assert report.results[1].score == pytest.approx(0.01)

    # Verify temporal metadata was added
    assert "reference_time" in report.results[0].metadata


@pytest.mark.asyncio
async def test_backtest_runner_parallel_concurrency(mock_orchestrator):
    r"""Ensures the semaphore correctly limits concurrency."""
    # We can't easily check timing here without complex mocking,
    # but we can verify it doesn't crash with many items.
    runner = BacktestRunner(mock_orchestrator, concurrency=2)

    items = [
        BacktestInstance(
            question=ForecastQuestion(id=f"q{i}", title="test"),
            resolution=ForecastResolution(question_id=f"q{i}", outcome="1"),
            reference_time=datetime(2024, 1, 1),
        )
        for i in range(10)
    ]

    dataset = BacktestDataset(items=items)
    report = await runner.run(dataset)

    assert report.total_evaluations == 10
