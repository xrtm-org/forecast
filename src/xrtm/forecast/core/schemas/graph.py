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

r"""Execution-graph state and temporal context schemas.

Defines ``BaseGraphState`` — the mutable state object that flows
through the orchestrator execution graph — and ``TemporalContext``
for temporal sandboxing during backtests.
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TemporalContext(BaseModel):
    r"""
    Metadata for temporal sandboxing during backtests.
    r"""

    reference_time: datetime = Field(description="The 'frozen' point in time for the forecast.")
    is_backtest: bool = Field(default=False, description="Whether the run is a historical backtest.")
    strict_mode: bool = Field(default=True, description="If True, tools MUST support PiT mode.")

    def now(self) -> datetime:
        r"""Returns the current effective time (simulated or real)."""
        if self.is_backtest:
            # We trust that freezegun is active if the orchestrator did its job,
            # but for safety/clarity, we return reference_time in strict logic.
            return self.reference_time
        return datetime.now()

    @property
    def today_str(self) -> str:
        r"""Returns YYYY-MM-DD string of the effective time."""
        return self.now().strftime("%Y-%m-%d")


class BaseGraphState(BaseModel):
    r"""
    A unified state object for tracking the forecast run lifecycle across an orchestrated execution graph.

    `BaseGraphState` carries the cumulative intelligence gathered by multiple
    agents, records execution traces, and provides operational context for loop control and performance tracking.

    Attributes:
        subject_id (`str`):
            The unique identifier for the subject being analyzed (e.g., question ID).
        node_reports (`Dict[str, Any]`):
            A generic storage bucket for outputs from various execution-graph nodes.
        past_critique (`str`):
            Stored feedback for iterative loops.
        cycle_count (`int`):
            Internal counter for the number of reasoning iterations performed.
        max_cycles (`int`):
            Maximum allowed cycles for the orchestrator.
        context (`Dict[str, Any]`):
            Global operational context provided during initialization.
        latencies (`Dict[str, float]`):
            Execution timing data for each node in seconds.
        usage (`Dict[str, int]`):
            Global token consumption statistics.
        execution_path (`List[str]`):
            The internal runtime field for the ordered execution trace.
        temporal_context (`Optional[TemporalContext]`):
            Context for temporal sandboxing, defining the reference time.
    r"""

    subject_id: str = Field(description="The unique identifier for the subject being analyzed.")

    # Generic bucket for node outputs to avoid hardcoded domain fields
    node_reports: Dict[str, Any] = Field(default_factory=dict)

    # Feedback & Loop Control
    past_critique: str = ""
    cycle_count: int = 0
    max_cycles: int = 3

    # Operational Context
    context: Dict[str, Any] = Field(default_factory=dict)

    # Performance & Diagnostics
    latencies: Dict[str, float] = Field(default_factory=dict)
    usage: Dict[str, int] = Field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )

    # Communication & Audit
    execution_path: List[str] = Field(
        default_factory=list,
        description="Ordered list of execution-graph node names executed. Prefer `execution_trace` in user-facing language.",
    )

    # Temporal Sandboxing
    temporal_context: Optional[TemporalContext] = Field(default=None, description="Metadata for temporal sandboxing.")

    # Prior State Injection (Decision 1)
    prior_state: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Beta-parameterized prior state for training injection. Structure: {alpha, beta, silence_delta, deadline_delta}",
    )

    # Rolling News Context (Decision 5)
    news_history: List[str] = Field(
        default_factory=list,
        description="Recent headlines for context/deduplication. Max ~20 items for token budget.",
    )

    # Merkle Integrity (Institutional Grade)
    state_hash: Optional[str] = Field(default=None, description="SHA-256 hash of the current state.")
    parent_hash: Optional[str] = Field(default=None, description="Hash of the preceding state in the reasoning chain.")

    @model_validator(mode="before")
    @classmethod
    def _apply_execution_trace_alias(cls, data: Any) -> Any:
        r"""Accept `execution_trace` as a compatibility alias for `execution_path`."""
        if not isinstance(data, dict) or "execution_trace" not in data or "execution_path" in data:
            return data

        updated = dict(data)
        updated["execution_path"] = updated["execution_trace"]
        return updated

    @property
    def execution_trace(self) -> List[str]:
        r"""Preferred user-facing alias for the ordered execution trace."""
        return self.execution_path

    @execution_trace.setter
    def execution_trace(self, value: List[str]) -> None:
        r"""Backward-compatible setter for the ordered execution trace."""
        self.execution_path = value

    def compute_hash(self) -> str:
        r"""
        Computes a deterministic SHA-256 hash of the current state.
        Excludes volatile fields like 'latencies' or 'usage' if desired,
        but for sovereignty we include everything that impacts the reasoning.
        """
        # We exclude the hash fields themselves from the computation
        # and volatile fields like latencies to ensure consistency across environments
        state_dict = self.model_dump(exclude={"state_hash", "parent_hash", "latencies", "usage"})

        # Use deterministic JSON serialization
        encoded = json.dumps(state_dict, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    model_config = ConfigDict(arbitrary_types_allowed=True)


__all__ = ["BaseGraphState"]
