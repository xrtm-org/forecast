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

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReasoningSchema(BaseModel):
    """Standardized unit of agentic thought."""

    claim: str = Field(description="The primary assertion or recommendation.")
    evidence: List[str] = Field(description="Key data points or facts supporting the claim.")
    risks: List[str] = Field(description="Potential risks, gaps, or counter-arguments identified.")
    rationale: str = Field(description="Step-by-step logic connecting evidence to claim.")
    causal_links: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Epistemic graph edges: [{'source': 'A', 'target': 'B', 'type': 'causes'}]",
    )


class Attribution(BaseModel):
    """Standardized metadata for agent contributions."""

    primary_driver: str
    associated_agent: str
    confidence: float = Field(ge=0.0, le=1.0)


class ConfidenceMetrics(BaseModel):
    """Standardized metadata for LLM confidence calibration."""

    verbal_confidence: float = 0.0
    signal_strength: float = 0.0
    entropy: float = 0.0
    hybrid_score: float = 0.0
    aggregation_method: str = "mean"


class CausalLink(BaseModel):
    """A single edge in a reasoning graph."""

    source: str
    target: str
    type: str = "causes"


class CausalPath(BaseModel):
    """A series of links forming a logical trajectory."""

    steps: List[str]
    links: List[CausalLink] = Field(default_factory=list)


class RippleEffect(BaseModel):
    """A second-order impact of an event."""

    trigger: str
    impact: str
    magnitude: str = "MEDIUM"  # LOW, MEDIUM, HIGH


class EpisodicExperience(BaseModel):
    """
    A single unit of learning. Represents a reasoning lifecycle.
    Decoupled from 'ticker' for library usage.
    """

    id: str = Field(description="Unique ID for this experience.")
    timestamp: str = Field(description="ISO format timestamp.")

    subject_id: str = Field(description="The primary subject (e.g. Ticker, UserID).")
    event_type: str = Field(description="Category of the event.")

    input_snapshot: Dict[str, Any] = Field(description="Context available during reasoning.")
    action_taken: str = Field(description="The chosen trajectory or decision.")

    reasoning: ReasoningSchema = Field(
        default_factory=lambda: ReasoningSchema(claim="N/A", evidence=[], risks=[], rationale="N/A")
    )
    confidence_metrics: ConfidenceMetrics = Field(default_factory=ConfidenceMetrics)

    outcome_score: Optional[float] = None
    realized_outcome: Optional[str] = None
    reflection: Optional[str] = None
