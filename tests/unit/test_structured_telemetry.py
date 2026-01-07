import json
import os

from forecast.telemetry.manager import TelemetryManager


def test_telemetry_trace_lifecycle():
    tm = TelemetryManager(log_dir="tests/logs/telemetry")
    trace_id = tm.start_trace()
    assert trace_id is not None
    assert tm._current_trace.trace_id == trace_id

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
    tm = TelemetryManager(log_dir="tests/logs/telemetry")
    tm.start_trace()
    with tm.start_span("test_export"):
        tm.add_event("export_event")

    path = tm.export_trace("test_trace.json")
    assert os.path.exists(path)

    with open(path, "r") as f:
        data = json.load(f)
        assert data["trace_id"] == tm._current_trace.trace_id
        assert len(data["spans"]) == 1
        assert data["spans"][0]["events"][0]["name"] == "export_event"

    # Cleanup
    os.remove(path)
