from datetime import datetime

import pytest

from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.forecast import ForecastOutput, ForecastQuestion, ForecastResolution
from forecast.core.schemas.graph import BaseGraphState
from forecast.kit.eval.runner import BacktestDataset, BacktestInstance, BacktestRunner


async def report_node(state: BaseGraphState, on_progress=None):
    # Determine what to report based on the subject_id
    if "output" in state.subject_id:
        state.node_reports["final"] = ForecastOutput(
            question_id=state.subject_id, confidence=0.85, reasoning="test reasoning"
        )
    elif "float" in state.subject_id:
        state.node_reports["final"] = 0.7
    elif "error" in state.subject_id:
        raise ValueError("Simulated error")
    return None


@pytest.fixture
def complex_orchestrator():
    orch = Orchestrator()
    orch.add_node("ingestion", report_node)
    orch.set_entry_point("ingestion")
    return orch


@pytest.mark.asyncio
async def test_backtest_runner_coverage_branches(complex_orchestrator):
    r"""Covers the remaining branches in BacktestRunner."""
    runner = BacktestRunner(complex_orchestrator)

    dataset = BacktestDataset(
        items=[
            # Branch: ForecastOutput
            BacktestInstance(
                question=ForecastQuestion(id="q_output", title="t", content="has context"),
                resolution=ForecastResolution(question_id="q_output", outcome="1"),
                reference_time=datetime(2024, 1, 1),
            ),
            # Branch: Float prediction
            BacktestInstance(
                question=ForecastQuestion(id="q_float", title="t"),
                resolution=ForecastResolution(question_id="q_float", outcome="0"),
                reference_time=datetime(2024, 1, 1),
            ),
            # Branch: Exception handling
            BacktestInstance(
                question=ForecastQuestion(id="q_error", title="t"),
                resolution=ForecastResolution(question_id="q_error", outcome="0"),
                reference_time=datetime(2024, 1, 1),
            ),
        ]
    )

    report = await runner.run(dataset)

    assert report.total_evaluations == 3
    # Verify the results
    # q_output (0.85 vs 1.0) -> BS = (0.15)^2 = 0.0225
    # q_float (0.7 vs 0.0) -> BS = (0.7)^2 = 0.49
    # q_error (0.5 vs 0.0) -> BS = (0.5)^2 = 0.25 (as coded in except block)

    res_map = {r.subject_id: r for r in report.results}
    assert res_map["q_output"].score == pytest.approx(0.0225)
    assert res_map["q_float"].score == pytest.approx(0.49)
    assert "error" in res_map["q_error"].metadata
