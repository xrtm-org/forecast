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

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SpanKind(str, Enum):
    r"""Category of a telemetry span, following OTel conventions."""

    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"


class TelemetryEvent(BaseModel):
    r"""
    A discrete event occurring within a reasoning span (e.g., a log, error, or data arrival).
    """

    name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: Dict[str, Any] = Field(default_factory=dict)


class TelemetrySpan(BaseModel):
    r"""
    A single unit of work within a trace, providing granular observability into agent execution.
    """

    name: str
    context: Dict[str, str] = Field(
        default_factory=lambda: {"trace_id": uuid.uuid4().hex, "span_id": uuid.uuid4().hex[:16]}
    )
    parent_id: Optional[str] = None
    kind: SpanKind = SpanKind.INTERNAL
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    status_code: str = "UNSET"  # UNSET, OK, ERROR
    status_message: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[TelemetryEvent] = Field(default_factory=list)
    _manager: Any = None

    def end(self, status_code: str = "OK", status_message: Optional[str] = None) -> None:
        r"""Marks the span as complete."""
        if not self.end_time:  # Prevent multiple ends
            self.end_time = datetime.now(timezone.utc)
            self.status_code = status_code
            self.status_message = status_message

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        mgr = self._manager
        if mgr is None:
            from forecast.telemetry.manager import telemetry_manager

            mgr = telemetry_manager

        status_code = "OK"
        status_message = None

        if exc_type:
            status_code = "ERROR"
            status_message = str(exc_val)
            self.add_event("exception", attributes={"message": status_message, "type": exc_type.__name__})

        mgr.end_span(status_code=status_code, status_message=status_message)

    def add_event(self, name: str, attributes: Optional[Dict] = None) -> None:
        r"""In-situ event logging within the span context."""
        event = TelemetryEvent(name=name, attributes=attributes or {})
        self.events.append(event)


class Trace(BaseModel):
    r"""
    A collection of spans representing a single, end-to-end reasoning flow.
    """

    trace_id: str
    spans: List[TelemetrySpan] = Field(default_factory=list)


__all__ = ["SpanKind", "TelemetryEvent", "TelemetrySpan", "Trace"]
