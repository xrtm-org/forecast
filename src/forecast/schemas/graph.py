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

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class BaseGraphState(BaseModel):
    r"""
    A unified state object for tracking the reasoning lifecycle across an orchestrated graph.

    `BaseGraphState` carries the cumulative intelligence gathered by multiple
    agents and provides operational context for loop control and performance tracking.

    Attributes:
        subject_id (`str`):
            The unique identifier for the subject being analyzed (e.g., question ID).
        node_reports (`Dict[str, Any]`):
            A generic storage bucket for outputs from various graph nodes.
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
            An ordered record of the agent/node sequence executed.
    """

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
    execution_path: List[str] = Field(default_factory=list, description="Ordered list of agent names executed.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


__all__ = ["BaseGraphState"]
