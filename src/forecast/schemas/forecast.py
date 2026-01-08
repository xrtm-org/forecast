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

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MetadataBase(BaseModel):
    r"""
    A foundational metadata block used to ensure consistency across schemas.

    Attributes:
        created_at (`datetime`):
            The timestamp when the object was created (defaults to UTC now).
        tags (`List[str]`):
            A list of searchable strings for categorization.
        market_type (`str`, *optional*):
            The category of the forecast market (e.g., "BINARY", "SCALAR").
        source_version (`str`, *optional*):
            The version of the data source providing the information.
        raw_data (`Dict[str, Any]`, *optional*):
            The original raw payload for auditing or reprocessing.
    """

    model_config = ConfigDict(extra="allow")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    market_type: Optional[str] = None
    source_version: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class ForecastQuestion(BaseModel):
    r"""
    The standardized input format for a forecasting task.

    `ForecastQuestion` is designed to be highly flexible, scaling from a simple
    text prompt to a structured market event with complex metadata.

    Attributes:
        id (`str`):
            A unique identifier for the question.
        title (`str`):
            The primary question or statement to be forecasted.
        content (`str`, *optional*):
            Detailed context, background information, or specific forecasting rules.
        metadata (`MetadataBase`):
            Operational metadata associated with the question.
    """

    id: str = Field(..., description="Unique identifier for the question")
    title: str = Field(..., description="The main question or content to forecast")
    content: Optional[str] = Field(None, description="Detailed context or prompt body")
    metadata: MetadataBase = Field(default_factory=MetadataBase)


class CausalNode(BaseModel):
    r"""
    Represents a single step in a logical reasoning chain.

    Attributes:
        event (`str`):
            The event or assumption in the causal sequence.
        probability (`float`, *optional*):
            The estimated probability of this specific event occurring.
        description (`str`, *optional*):
            A narrative explanation of why this event is included in the chain.
    """

    event: str = Field(..., description="The assumption or event in the chain")
    probability: Optional[float] = Field(None, ge=0, le=1)
    description: Optional[str] = None


class ForecastOutput(BaseModel):
    r"""
    The structured result of an agent's forecasting reasoning.

    Includes a "Dual-Trace" architecture:
    1. **Logical Trace**: A Bayesian-style sequence of assumptions (the Mental Model).
    2. **Structural Trace**: An audit trail of the actual agents/nodes executed.

    Attributes:
        question_id (`str`):
            Reference to the original `ForecastQuestion`.
        confidence (`float`):
            The final probability assigned to the primary outcome [0, 1].
        reasoning (`str`):
            The comprehensive narrative argument supporting the confidence score.
        logical_trace (`List[CausalNode]`):
            The causal assumptions identified by the model.
        structural_trace (`List[str]`):
            The names of the platform components (Agents, Skills) that processed this.
        metadata (`Dict[str, Any]`):
            Diagnostic metadata (latency, token usage, cost).
    """

    question_id: str
    confidence: float = Field(..., ge=0, le=1, description="Probability of the primary outcome")
    reasoning: str = Field(..., description="Narrative reasoning for the forecast")

    logical_trace: List[CausalNode] = Field(
        default_factory=list, description="The Bayesian-style sequence of assumptions (Mental Model)"
    )
    structural_trace: List[str] = Field(default_factory=list, description="Order of graph nodes executed (Audit Trail)")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Model info, latency, usage, cost")


class ForecastResolution(BaseModel):
    r"""
    The ground-truth outcome used to evaluate forecast accuracy.

    Attributes:
        question_id (`str`):
            Reference to the original `ForecastQuestion`.
        outcome (`str`):
            The final verified result or value.
        resolved_at (`datetime`):
            The timestamp when the outcome was finalized.
        metadata (`Dict[str, Any]`):
            Source verification info and resolution method.
    """

    question_id: str
    outcome: str = Field(..., description="The final winning outcome or value")
    resolved_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source info, verification method")


__all__ = ["MetadataBase", "ForecastQuestion", "CausalNode", "ForecastOutput", "ForecastResolution"]
