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

import contextvars
import logging
import os
import uuid
from typing import Dict, List, Optional

from forecast.telemetry.config import TelemetryConfig
from forecast.telemetry.schemas import SpanKind, TelemetryEvent, TelemetrySpan, Trace

logger = logging.getLogger(__name__)

# Context variables for thread/task-local telemetry state
_current_trace_var: contextvars.ContextVar[Optional[Trace]] = contextvars.ContextVar("current_trace", default=None)
_span_stack_var: contextvars.ContextVar[List[TelemetrySpan]] = contextvars.ContextVar("span_stack", default=[])


class TelemetryManager:
    r"""
    A management layer for structured telemetry and observability.

    `TelemetryManager` coordinates the lifecycle of traces and spans, ensuring
    alignment with OpenTelemetry standards. It provides utilities for tracking
    agent execution paths and exporting results for auditing.

    This implementation uses `contextvars` to ensure that traces and spans are
    isolated to the current execution task, preventing leakage in parallel environments.

    Args:
        log_dir (`str`, *optional*, defaults to `"logs/telemetry"`):
            The directory where telemetry traces will be exported.
    """

    def __init__(self, log_dir: str = "logs/telemetry", config: Optional[TelemetryConfig] = None):
        self.log_dir = log_dir
        self.config = config or TelemetryConfig()
        os.makedirs(self.log_dir, exist_ok=True)

    @property
    def current_trace(self) -> Optional[Trace]:
        r"""Returns the trace instance for the current context."""
        return _current_trace_var.get()

    @property
    def span_stack(self) -> List[TelemetrySpan]:
        r"""Returns the span stack for the current context."""
        # Note: Return a copy to prevent accidental mutation of the default value
        return list(_span_stack_var.get())

    def start_trace(self, trace_id: Optional[str] = None) -> str:
        r"""
        Initializes a new trace context for the current task.

        Args:
            trace_id (`str`, *optional*):
                A specific trace ID to use. If `None`, a new UUID is generated.

        Returns:
            `str`: The unique identifier for the new trace.
        """
        tid = trace_id or uuid.uuid4().hex
        trace = Trace(trace_id=tid)
        _current_trace_var.set(trace)
        _span_stack_var.set([])
        logger.debug(f"Started new task-local telemetry trace: {tid}")
        return tid

    def start_span(
        self, name: str, kind: SpanKind = SpanKind.INTERNAL, attributes: Optional[Dict] = None
    ) -> TelemetrySpan:
        r"""
        Creates and starts a new span within the current task's trace.

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
        trace = self.current_trace
        if not trace:
            self.start_trace()
            trace = self.current_trace

        stack = self.span_stack
        parent_id = stack[-1].context["span_id"] if stack else None

        span = TelemetrySpan(name=name, kind=kind, parent_id=parent_id, attributes=attributes or {})
        span._manager = self

        # Attach to the local trace
        if trace is not None:
            span.context["trace_id"] = trace.trace_id
            stack.append(span)
            _span_stack_var.set(stack)
            trace.spans.append(span)

        return span

    def end_span(self, status_code: str = "OK", status_message: Optional[str] = None) -> None:
        r"""
        Terminates the current active span in the local context.

        Args:
            status_code (`str`, *optional*, defaults to `"OK"`):
                The final status of the span (OK, ERROR).
            status_message (`str`, *optional*):
                An optional message describing the status.
        """
        stack = self.span_stack
        if not stack:
            logger.warning("Attempted to end a span but none are active in this context.")
            return

        span = stack.pop()
        _span_stack_var.set(stack)
        span.end(status_code=status_code, status_message=status_message)

    def add_event(self, name: str, attributes: Optional[Dict] = None) -> None:
        r"""
        Logs an event to the currently active span in the local context.

        Args:
            name (`str`):
                The name of the event.
            attributes (`Dict`, *optional*):
                Metadata associated with the event.
        """
        stack = self.span_stack
        if not stack:
            logger.warning("Attempted to add an event but no span is active in this context.")
            return

        event = TelemetryEvent(name=name, attributes=attributes or {})
        stack[-1].events.append(event)

    def export_trace(self, filename: Optional[str] = None) -> str:
        r"""
        Serializes and exports the current active trace to a JSON file.

        Args:
            filename (`str`, *optional*):
                The name of the file to write. Defaults to `trace_{id}.json`.

        Returns:
            `str`: The absolute path to the exported trace file.
        """
        trace = self.current_trace
        if not trace:
            logger.warning("Attempted to export trace but no trace is active.")
            return ""

        fname = filename or f"trace_{trace.trace_id}.json"
        path = os.path.join(self.log_dir, fname)

        try:
            with open(path, "w") as f:
                f.write(trace.model_dump_json(indent=2))
            logger.info(f"Telemetry trace exported: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to export telemetry trace: {e}")
            return ""


class trace_context:
    r"""
    A context manager for scoping a telemetry trace to a code block.

    This ensures that the trace is automatically started and optionally exported
    at the end of execution.

    Args:
        manager (`TelemetryManager`, *optional*):
            The manager instance to use. Defaults to the global singleton.
        trace_id (`str`, *optional*):
            An explicit trace ID to use.
        export (`bool`, *optional*, defaults to `False`):
            Whether to automatically export the trace to JSON on exit.

    Example:
        ```python
        >>> with trace_context(export=True):
        ...     # All telemetry within this block is isolated
        ...     agent.run(...)
        ```
    """

    def __init__(
        self,
        manager: Optional[TelemetryManager] = None,
        trace_id: Optional[str] = None,
        export: bool = False,
    ):
        self.manager = manager or telemetry_manager
        self.trace_id = trace_id
        self.export = export
        self._token = None

    def __enter__(self):
        self.manager.start_trace(self.trace_id)
        return self.manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.export:
            self.manager.export_trace()
        # ContextVar cleanup is handled by the framework but we could set back to None here
        _current_trace_var.set(None)
        _span_stack_var.set([])


# Global singleton
telemetry_manager = TelemetryManager()

__all__ = ["TelemetryManager", "telemetry_manager", "trace_context"]
