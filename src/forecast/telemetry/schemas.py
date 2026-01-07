import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SpanKind(str, Enum):
    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"

class TelemetryEvent(BaseModel):
    """
    An event within a span (e.g., log message, exception).
    """
    name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    attributes: Dict[str, Any] = Field(default_factory=dict)

class TelemetrySpan(BaseModel):
    """
    A single unit of work in a trace, compatible with OpenTelemetry.
    """
    name: str
    context: Dict[str, str] = Field(
        default_factory=lambda: {
            "trace_id": uuid.uuid4().hex,
            "span_id": uuid.uuid4().hex[:16]
        }
    )
    parent_id: Optional[str] = None
    kind: SpanKind = SpanKind.INTERNAL
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status_code: str = "UNSET" # UNSET, OK, ERROR
    status_message: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[TelemetryEvent] = Field(default_factory=list)
    _manager: Any = None

    def end(self, status_code: str = "OK", status_message: Optional[str] = None):
        if not self.end_time: # Prevent multiple ends
            self.end_time = datetime.utcnow()
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

    def add_event(self, name: str, attributes: Optional[Dict] = None):
        event = TelemetryEvent(name=name, attributes=attributes or {})
        self.events.append(event)

class Trace(BaseModel):
    """
    A collection of spans representing a single reasoning flow.
    """
    trace_id: str
    spans: List[TelemetrySpan] = Field(default_factory=list)
