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

from unittest.mock import MagicMock, patch

import pytest

from forecast.core.eval.definitions import EvaluationReport, EvaluationResult
from forecast.core.schemas.graph import BaseGraphState
from forecast.kit.eval.analytics import SliceAnalytics
from forecast.kit.eval.backtester import Backtester
from forecast.kit.eval.replayer import TraceReplayer


def test_definitions_to_json(tmp_path):
    """Verify to_json coverage."""
    path = tmp_path / "report.json"
    report = EvaluationReport(metric_name="test", mean_score=0.5, total_evaluations=1, results=[])
    report.to_json(str(path))
    assert path.exists()


def test_definitions_to_pandas_success():
    """Verify to_pandas works when pandas is installed."""
    res = EvaluationResult(subject_id="q1", score=0.1, ground_truth=1, prediction=0.9)
    report = EvaluationReport(metric_name="test", mean_score=0.1, total_evaluations=1, results=[res])
    with patch("pandas.DataFrame") as mock_df:
        report.to_pandas()
        mock_df.assert_called_once()


def test_definitions_to_pandas_import_error():
    """Verify to_pandas handles missing pandas gracefully."""
    report = EvaluationReport(metric_name="test", mean_score=0.5, total_evaluations=0, results=[])
    with patch.dict("sys.modules", {"pandas": None}):
        with pytest.raises(ImportError, match="Pandas is required"):
            report.to_pandas()


def test_analytics_empty_slice_handling():
    """Trigger the 'count == 0' branch (highly defensive) or invalid grouping."""
    # This is hard to trigger via public API because slices are only created if results exist.
    # We'll use a mock if necessary, but we can also verify the logic handles missing tags.
    results = [EvaluationResult(subject_id="q1", score=0.1, ground_truth=1, prediction=0.9, metadata={})]
    reports = SliceAnalytics.compute_slices(results)
    assert len(reports) == 0


def test_analytics_ece_failure_handling():
    """Trigger ECE computation failure branch."""
    results = [
        EvaluationResult(
            subject_id="q1",
            score=0.1,
            ground_truth=1,
            prediction=0.9,
            metadata={"tags": ["fail"]},
        )
    ]
    with patch("forecast.kit.eval.analytics.ExpectedCalibrationErrorEvaluator.compute_calibration_data") as mock_ece:
        mock_ece.side_effect = Exception("Mock ECE Failure")
        reports = SliceAnalytics.compute_slices(results)
        assert "tag:fail" in reports
        assert reports["tag:fail"].summary_statistics["ece"] == 0.0


def test_replayer_full_cycle(tmp_path):
    """Verify full save-load-replay cycle for coverage."""
    replayer = TraceReplayer()
    path = tmp_path / "trace.json"

    # 1. Prepare State
    state = BaseGraphState(subject_id="q1")
    state.node_reports["final"] = {"confidence": 0.8}

    # 2. Save
    replayer.save_trace(state, str(path))
    assert path.exists()

    # 3. Load
    loaded = replayer.load_trace(str(path))
    assert loaded.subject_id == "q1"

    # 4. Replay
    # We need to mock BacktestRunner to avoid integration overhead, but the logic should run.
    with patch("forecast.kit.eval.replayer.BacktestRunner") as mock_runner_cls:
        mock_runner = mock_runner_cls.return_value
        mock_result = EvaluationResult(subject_id="q1", score=0.1, ground_truth=1, prediction=0.8)
        mock_runner.evaluate_state.return_value = mock_result

        # Test with float resolution
        res = replayer.replay_evaluation(str(path), resolution=1.0)
        assert res.score == 0.1
        assert res.metadata["is_replay"] is True

        # Test with resolution object
        from forecast.core.schemas.forecast import ForecastResolution

        res_obj = ForecastResolution(question_id="q1", outcome="1.0")
        res2 = replayer.replay_evaluation(str(path), resolution=res_obj)
        assert res2.score == 0.1


def test_replayer_save_load_errors(tmp_path):
    """Verify error handling in TraceReplayer."""
    replayer = TraceReplayer()

    # Save error (using a directory as file path to trigger exception)
    invalid_dir = tmp_path / "dir"
    invalid_dir.mkdir()
    with pytest.raises(Exception):
        replayer.save_trace(BaseGraphState(subject_id="test"), str(invalid_dir))

    # Load error (invalid json)
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("invalid json")
    with pytest.raises(Exception):
        replayer.load_trace(str(bad_json))


def test_backtester_edge_cases():
    """Verify Backtester catches exceptions and handles empty data."""
    agent = MagicMock()
    evaluator = MagicMock()
    backtester = Backtester(agent, evaluator)

    # Empty dataset
    report = pytest.mark.asyncio(backtester.run([]))
    # Note: Using asyncio run for the coroutine
    import asyncio

    report = asyncio.run(backtester.run([]))
    assert report.total_evaluations == 0
    assert report.mean_score == 0.0

    # Exception in loop
    mock_question = MagicMock()
    mock_question.id = "error_q"
    dataset = [(mock_question, MagicMock())]
    agent.run.side_effect = Exception("Agent Crash")

    report = asyncio.run(backtester.run(dataset))
    assert report.total_evaluations == 0  # None succeeded


@pytest.mark.asyncio
async def test_backtester_confidence_getattr():
    """Verify getattr(prediction, 'confidence', prediction) logic."""
    agent = MagicMock()
    # Mocking as AsyncMock for await
    from unittest.mock import AsyncMock

    agent.run = AsyncMock()

    # Case 1: Prediction is a simple float
    agent.run.return_value = 0.85
    evaluator = MagicMock()
    evaluator.evaluate.return_value = EvaluationResult(subject_id="q1", score=0.1, ground_truth=1, prediction=0.85)

    backtester = Backtester(agent, evaluator)
    dataset = [(MagicMock(id="q1"), MagicMock(outcome=1))]
    await backtester.run(dataset)

    evaluator.evaluate.assert_called_with(prediction=0.85, ground_truth=1, subject_id="q1")

    # Case 2: Prediction is an object with 'confidence' attribute
    mock_output = MagicMock()
    mock_output.confidence = 0.92
    agent.run.return_value = mock_output

    await backtester.run(dataset)
    evaluator.evaluate.assert_called_with(prediction=0.92, ground_truth=1, subject_id="q1")
