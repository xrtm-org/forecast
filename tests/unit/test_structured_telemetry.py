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
import os

from forecast.telemetry.manager import TelemetryManager


def test_telemetry_trace_lifecycle():
    r"""
    Verifies that traces and spans are correctly captured by the TelemetryManager.
    """
    tm = TelemetryManager(log_dir="tests/logs/telemetry")
    trace_id = tm.start_trace()
    assert trace_id is not None
    assert tm.current_trace is not None
    assert tm.current_trace.trace_id == trace_id

    # Root span
    with tm.start_span("root_span") as span:
        assert span.name == "root_span"
        assert span.context["trace_id"] == trace_id

        # Child span
        with tm.start_span("child_span") as child:
            assert child.parent_id == span.context["span_id"]
            tm.add_event("child_event", attributes={"key": "val"})
            assert len(child.events) == 1

    # Verify spans are closed
    assert span.end_time is not None
    assert child.end_time is not None


def test_telemetry_export():
    r"""
    Verifies that captured traces can be exported to JSON files.
    """
    tm = TelemetryManager(log_dir="tests/logs/telemetry")
    trace_id = tm.start_trace()
    with tm.start_span("test_export"):
        tm.add_event("export_event")

    path = tm.export_trace("test_trace.json")
    assert os.path.exists(path)

    with open(path, "r") as f:
        data = json.load(f)
        assert data["trace_id"] == trace_id
        assert len(data["spans"]) == 1
        assert data["spans"][0]["events"][0]["name"] == "export_event"

    # Cleanup
    os.remove(path)
