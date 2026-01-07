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

import logging
import os
import uuid
from typing import Dict, List, Optional

from forecast.telemetry.schemas import SpanKind, TelemetryEvent, TelemetrySpan, Trace

logger = logging.getLogger(__name__)


class TelemetryManager:
    r"""
    A management layer for structured telemetry and observability.

    `TelemetryManager` coordinates the lifecycle of traces and spans, ensuring
    alignment with OpenTelemetry standards. It provides utilities for tracking
    agent execution paths and exporting results for auditing.

    Args:
        log_dir (`str`, *optional*, defaults to `"logs/telemetry"`):
            The directory where telemetry traces will be exported.
    """

    def __init__(self, log_dir: str = "logs/telemetry"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self._current_trace: Optional[Trace] = None
        self._span_stack: List[TelemetrySpan] = []

    def start_trace(self) -> str:
        r"""
        Initializes a new global trace context.

        Returns:
            `str`: The unique identifier for the new trace.
        """
        trace_id = uuid.uuid4().hex
        self._current_trace = Trace(trace_id=trace_id)
        self._span_stack = []
        logger.debug(f"Started new telemetry trace: {trace_id}")
        return trace_id

    def start_span(
        self, name: str, kind: SpanKind = SpanKind.INTERNAL, attributes: Optional[Dict] = None
    ) -> TelemetrySpan:
        r"""
        Creates and starts a new span, making it the current active context.

        Args:
            name (`str`):
                The logical name of the span (e.g., "reasoning_step").
            kind (`SpanKind`, *optional*, defaults to `INTERNAL`):
                The category of the span (INTERNAL, SERVER, CLIENT, etc.).
            attributes (`Dict`, *optional*):
                Metadata to attach to the span.

        Returns:
            `TelemetrySpan`: The newly created span instance.
        """
        if not self._current_trace:
            self.start_trace()

        parent_id = self._span_stack[-1].context["span_id"] if self._span_stack else None

        span = TelemetrySpan(name=name, kind=kind, parent_id=parent_id, attributes=attributes or {})
        span._manager = self

        # Ensure trace ID matches the current trace
        if self._current_trace is not None:
            span.context["trace_id"] = self._current_trace.trace_id
            self._span_stack.append(span)
            self._current_trace.spans.append(span)
        return span

    def end_span(self, status_code: str = "OK", status_message: Optional[str] = None) -> None:
        r"""
        Terminates the current active span and updates its status.

        Args:
            status_code (`str`, *optional*, defaults to `"OK"`):
                The final status of the span (OK, ERROR).
            status_message (`str`, *optional*):
                An optional message describing the status.
        """
        if not self._span_stack:
            logger.warning("Attempted to end a span but none are active.")
            return

        span = self._span_stack.pop()
        span.end(status_code=status_code, status_message=status_message)

    def add_event(self, name: str, attributes: Optional[Dict] = None) -> None:
        r"""
        Logs an event to the currently active span.

        Args:
            name (`str`):
                The name of the event.
            attributes (`Dict`, *optional*):
                Metadata associated with the event.
        """
        if not self._span_stack:
            logger.warning("Attempted to add an event but no span is active.")
            return

        event = TelemetryEvent(name=name, attributes=attributes or {})
        self._span_stack[-1].events.append(event)

    def export_trace(self, filename: Optional[str] = None) -> str:
        r"""
        Serializes and exports the current trace to a JSON file.

        Args:
            filename (`str`, *optional*):
                The name of the file to write. Defaults to `trace_{id}.json`.

        Returns:
            `str`: The absolute path to the exported trace file.
        """
        if not self._current_trace:
            return ""

        fname = filename or f"trace_{self._current_trace.trace_id}.json"
        path = os.path.join(self.log_dir, fname)

        try:
            with open(path, "w") as f:
                f.write(self._current_trace.model_dump_json(indent=2))
            logger.info(f"Telemetry trace exported: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to export telemetry trace: {e}")
            return ""


# Global singleton
telemetry_manager = TelemetryManager()

__all__ = ["TelemetryManager", "telemetry_manager"]
