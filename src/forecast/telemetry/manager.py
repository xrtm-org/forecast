import logging
import os
import uuid
from typing import Dict, List, Optional

from forecast.telemetry.schemas import SpanKind, TelemetryEvent, TelemetrySpan, Trace

logger = logging.getLogger(__name__)

class TelemetryManager:
    """
    Manages structured telemetry for the forecasting engine.
    Compatible with OpenTelemetry standards.
    """
    def __init__(self, log_dir: str = "logs/telemetry"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self._current_trace: Optional[Trace] = None
        self._span_stack: List[TelemetrySpan] = []

    def start_trace(self) -> str:
        """Starts a new global trace."""
        trace_id = uuid.uuid4().hex
        self._current_trace = Trace(trace_id=trace_id)
        self._span_stack = []
        logger.debug(f"Started new telemetry trace: {trace_id}")
        return trace_id

    def start_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL, attributes: Optional[Dict] = None) -> TelemetrySpan:
        """Starts a new span as a child of the current span (if any)."""
        if not self._current_trace:
            self.start_trace()

        parent_id = self._span_stack[-1].context["span_id"] if self._span_stack else None

        span = TelemetrySpan(
            name=name,
            kind=kind,
            parent_id=parent_id,
            attributes=attributes or {}
        )
        span._manager = self

        # Ensure trace ID matches the current trace
        if self._current_trace is not None:
            span.context["trace_id"] = self._current_trace.trace_id
            self._span_stack.append(span)
            self._current_trace.spans.append(span)
        return span

    def end_span(self, status_code: str = "OK", status_message: Optional[str] = None):
        """Ends the current active span."""
        if not self._span_stack:
            logger.warning("Attempted to end a span but none are active.")
            return

        span = self._span_stack.pop()
        span.end(status_code=status_code, status_message=status_message)

    def add_event(self, name: str, attributes: Optional[Dict] = None):
        """Adds an event to the current active span."""
        if not self._span_stack:
            logger.warning("Attempted to add an event but no span is active.")
            return

        event = TelemetryEvent(name=name, attributes=attributes or {})
        self._span_stack[-1].events.append(event)

    def export_trace(self, filename: Optional[str] = None) -> str:
        """Exports the current trace to a JSON file."""
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
