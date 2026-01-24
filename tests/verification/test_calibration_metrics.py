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

import json
from datetime import datetime
from typing import Any, Optional

import pytest

from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.schemas.forecast import ForecastQuestion, ForecastResolution
from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.kit.eval.runner import BacktestDataset, BacktestInstance, BacktestRunner


class MockOrchestrator(Orchestrator):
    def __init__(self, predictions):
        super().__init__()
        self.predictions = predictions  # Map subject_id -> confidence
        self.call_count = 0

    async def run(
        self,
        state: BaseGraphState,
        entry_node: str = "ingestion",
        on_progress: Optional[Any] = None,
        stopwatch: Optional[Any] = None,
    ) -> BaseGraphState:
        self.call_count += 1
        # Inject the pre-determined prediction for this subject
        conf = self.predictions.get(state.subject_id, 0.5)
        # Simulate simple dict report
        state.node_reports["final"] = {"confidence": conf}
        return state


@pytest.mark.asyncio
async def test_brier_and_ece_verification(tmp_path):
    print(">>> Starting Verification for Calibration Suite")

    dataset_items = []

    # Group A: High Confidence (0.9), Low Accuracy (0.0) -> High ECE
    from xrtm.forecast.core.schemas.forecast import MetadataBase

    for i in range(5):
        q_id = f"q_overconf_{i}"
        dataset_items.append(
            BacktestInstance(
                question=ForecastQuestion(id=q_id, title="Masked", metadata=MetadataBase(subject_type="BINARY")),
                resolution=ForecastResolution(question_id=q_id, outcome="0.0"),  # WRONG outcome
                reference_time=datetime(2025, 1, 1),
                tags=["group:overconfident"],
            )
        )

    # Group B: Perfect Calibration (0.8 confidence, 0.8 accuracy) requires large N,
    # let's just do: Confidence 0.8, Outcome 1.0 (4 times) and 0.0 (1 time) -> 80% accuracy
    for i in range(5):
        q_id = f"q_calib_{i}"
        outcome_val = "1.0" if i < 4 else "0.0"  # 4/5 = 80% accuracy
        dataset_items.append(
            BacktestInstance(
                question=ForecastQuestion(id=q_id, title="Masked", metadata=MetadataBase(subject_type="BINARY")),
                resolution=ForecastResolution(question_id=q_id, outcome=outcome_val),
                reference_time=datetime(2025, 1, 1),
                tags=["group:calibrated"],
            )
        )

    predictions = {}
    for item in dataset_items:
        if "overconf" in item.question.id:
            predictions[item.question.id] = 0.9
        else:
            predictions[item.question.id] = 0.8

    dataset = BacktestDataset(items=dataset_items)

    # 2. Run Backtest
    print(f"Running backtest on {len(dataset_items)} items...")

    # Hack: Inject mock orchestrator
    mock_orch = MockOrchestrator(predictions)
    runner = BacktestRunner(orchestrator=mock_orch)

    report = await runner.run(dataset)

    # 3. Verify ECE Calculation
    print("\n--- ECE Verification ---")
    ece = report.summary_statistics.get("ece")
    print(f"Global ECE Score: {ece}")

    assert ece is not None, "ECE score not found in summary metrics"
    assert ece > 0.0, "ECE should be positive for imperfect model"

    # Manual ECE check
    # Bin 0.9: 5 items. Conf=0.9, Acc=0.0. Diff=0.9. Weight=5/10=0.5. Contrib = 0.45
    # Bin 0.8: 5 items. Conf=0.8, Acc=0.8. Diff=0.0. Weight=0.5. Contrib = 0.0
    # Expected ECE ~ 0.45
    print(f"Expected ECE ~ 0.45. Actual: {ece}")
    assert 0.44 < ece < 0.46, f"ECE calculation incorrect. Got {ece}"

    # 4. Verify Reliability Bins
    print("\n--- Reliability Bin Verification ---")
    bins = report.reliability_bins
    assert bins is not None
    assert len(bins) > 0

    found_overconf_bin = False
    for b in bins:
        if b.count > 0:
            print(
                f"Bin {b.bin_center:.2f}: Count={b.count}, Pred={b.mean_prediction:.2f}, Acc={b.mean_ground_truth:.2f}"
            )
            if 0.90 <= b.bin_center <= 1.0:  # The 0.9 bin (center 0.95)
                found_overconf_bin = True
                assert b.count == 5
                assert abs(b.mean_prediction - 0.9) < 1e-5
                assert abs(b.mean_ground_truth - 0.0) < 1e-5

    assert found_overconf_bin, "Did not find the expected overconfident bin"

    # 5. Verify Metadata & Exports
    print("\n--- Export Verification ---")

    # JSON Export
    json_path = tmp_path / "test_calibration_report.json"
    report.to_json(str(json_path))
    with open(json_path, "r") as f:
        data = json.load(f)
        assert data["summary_statistics"]["ece"] == ece
        assert len(data["reliability_bins"]) > 0
        assert "tags" in data["results"][0]["metadata"]
        print("JSON export verified.")

    # 6. Verify Tags
    assert report.results[0].metadata["tags"] == ["group:overconfident"]
    print("Metadata propagation verified.")

    print("\n>>> Verification SUCCESS!")
