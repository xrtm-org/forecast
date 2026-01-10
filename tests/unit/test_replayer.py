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

import pytest

from forecast.core.schemas.graph import BaseGraphState, TemporalContext
from forecast.kit.eval.replayer import TraceReplayer


class MockState(BaseGraphState):
    pass


def test_trace_serialization(tmp_path):
    """Verify save and load round-trip."""
    file_path = tmp_path / "trace.json"

    # 1. Create State
    state = MockState(
        subject_id="test-1",
        context={"env": "test"},
        node_reports={"node_a": {"confidence": 0.8}},
        temporal_context=TemporalContext(reference_time=datetime(2024, 1, 1), is_backtest=True),
    )

    # 2. Save
    TraceReplayer.save_trace(state, str(file_path))

    assert file_path.exists()

    # 3. Load
    loaded_state = TraceReplayer.load_trace(str(file_path))

    # 4. Assert Equivalence
    assert loaded_state.subject_id == state.subject_id
    # Note: loaded_state will be BaseGraphState unless we use TypeAdapter logic or explicit subclass loading
    # TraceReplayer currently loads as BaseGraphState, which is fine as strict typing isn't enforcing subclass
    assert loaded_state.node_reports["node_a"] == {"confidence": 0.8}
    assert loaded_state.temporal_context.reference_time == state.temporal_context.reference_time


def test_replay_evaluation(tmp_path):
    """Verify replay logic correctly scores a loaded trace."""
    file_path = tmp_path / "trace_score.json"

    # 1. Create State with a "Forecast"
    # We use a dict in node_reports to mimic a ForecastOutput serializable form
    state = MockState(subject_id="test-score", node_reports={"final": {"confidence": 0.9}})
    TraceReplayer.save_trace(state, str(file_path))

    # 2. Replay with Ground Truth = 1.0 (True)
    replayer = TraceReplayer()
    result = replayer.replay_evaluation(trace_path=str(file_path), resolution="True")

    # 3. Validation
    # Brier Score = (0.9 - 1.0)^2 = (-0.1)^2 = 0.01
    assert result.score == pytest.approx(0.01)
    assert result.metadata["is_replay"] is True
    assert result.subject_id == "test-score"
