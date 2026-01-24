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

r"""Unit tests for forecast.core.telemetry.manager."""

from xrtm.forecast.core.telemetry.manager import TelemetryManager, trace_context
from xrtm.forecast.core.telemetry.schemas import SpanKind


class TestTelemetryManager:
    r"""Tests for the TelemetryManager class."""

    def test_init_creates_log_dir(self, tmp_path):
        r"""Should create log directory on init."""
        log_dir = tmp_path / "telemetry_logs"
        # Initialize
        TelemetryManager(log_dir=str(log_dir))

        assert log_dir.exists()

    def test_start_trace(self, tmp_path):
        r"""Should start a new trace."""
        manager = TelemetryManager(log_dir=str(tmp_path))

        trace_id = manager.start_trace()

        assert trace_id is not None
        assert len(trace_id) == 32  # UUID hex

    def test_start_trace_with_custom_id(self, tmp_path):
        r"""Should use provided trace ID."""
        manager = TelemetryManager(log_dir=str(tmp_path))

        trace_id = manager.start_trace("custom_trace_id")

        assert trace_id == "custom_trace_id"

    def test_current_trace_property(self, tmp_path):
        r"""Should return current trace after start."""
        manager = TelemetryManager(log_dir=str(tmp_path))
        manager.start_trace("test_trace")

        assert manager.current_trace is not None
        assert manager.current_trace.trace_id == "test_trace"

    def test_start_span(self, tmp_path):
        r"""Should create a span within current trace."""
        manager = TelemetryManager(log_dir=str(tmp_path))
        manager.start_trace()

        span = manager.start_span("test_span")

        assert span is not None
        assert span.name == "test_span"
        assert len(manager.span_stack) == 1

    def test_start_span_auto_creates_trace(self, tmp_path):
        r"""Should auto-create trace if none exists."""
        manager = TelemetryManager(log_dir=str(tmp_path))

        span = manager.start_span("auto_span")

        assert span is not None
        assert manager.current_trace is not None

    def test_start_span_with_kind(self, tmp_path):
        r"""Should set span kind."""
        manager = TelemetryManager(log_dir=str(tmp_path))
        manager.start_trace()

        span = manager.start_span("client_span", kind=SpanKind.CLIENT)

        assert span.kind == SpanKind.CLIENT

    def test_start_span_with_attributes(self, tmp_path):
        r"""Should set span attributes."""
        manager = TelemetryManager(log_dir=str(tmp_path))
        manager.start_trace()

        span = manager.start_span("attr_span", attributes={"key": "value"})

        assert span.attributes["key"] == "value"

    def test_nested_spans(self, tmp_path):
        r"""Should support nested spans with parent IDs."""
        manager = TelemetryManager(log_dir=str(tmp_path))
        manager.start_trace()

        parent = manager.start_span("parent")
        child = manager.start_span("child")

        assert child.parent_id == parent.context["span_id"]
        assert len(manager.span_stack) == 2

    def test_end_span(self, tmp_path):
        r"""Should end active span."""
        manager = TelemetryManager(log_dir=str(tmp_path))
        manager.start_trace()
        manager.start_span("test_span")

        manager.end_span()

        assert len(manager.span_stack) == 0

    def test_end_span_no_active(self, tmp_path):
        r"""Should handle ending span when none active."""
        manager = TelemetryManager(log_dir=str(tmp_path))
        manager.start_trace()

        # Should not raise
        manager.end_span()

    def test_add_event(self, tmp_path):
        r"""Should add event to active span."""
        manager = TelemetryManager(log_dir=str(tmp_path))
        manager.start_trace()
        manager.start_span("span")

        manager.add_event("test_event", {"attr": "value"})

        stack = manager.span_stack
        assert len(stack[-1].events) == 1
        assert stack[-1].events[0].name == "test_event"

    def test_add_event_no_active_span(self, tmp_path):
        r"""Should handle adding event when no span active."""
        manager = TelemetryManager(log_dir=str(tmp_path))
        manager.start_trace()

        # Should not raise
        manager.add_event("orphan_event")

    def test_export_trace(self, tmp_path):
        r"""Should export trace to JSON file."""
        manager = TelemetryManager(log_dir=str(tmp_path))
        manager.start_trace("export_test")
        manager.start_span("test_span")
        manager.end_span()

        filepath = manager.export_trace()

        assert filepath != ""
        assert (tmp_path / "trace_export_test.json").exists()

    def test_export_trace_no_active(self, tmp_path):
        r"""Should handle export when no trace active."""
        # Clear any leftover context from previous tests
        from xrtm.forecast.core.telemetry.manager import _current_trace_var, _span_stack_var

        _current_trace_var.set(None)
        _span_stack_var.set([])

        manager = TelemetryManager(log_dir=str(tmp_path))

        filepath = manager.export_trace()

        assert filepath == ""


class TestTraceContext:
    r"""Tests for the trace_context context manager."""

    def test_context_manager(self, tmp_path):
        r"""Should start and cleanup trace."""
        manager = TelemetryManager(log_dir=str(tmp_path))

        with trace_context(manager=manager):
            assert manager.current_trace is not None

    def test_context_manager_with_export(self, tmp_path):
        r"""Should export trace on exit when export=True."""
        manager = TelemetryManager(log_dir=str(tmp_path))

        with trace_context(manager=manager, trace_id="export_ctx", export=True):
            manager.start_span("span")
            manager.end_span()

        assert (tmp_path / "trace_export_ctx.json").exists()
