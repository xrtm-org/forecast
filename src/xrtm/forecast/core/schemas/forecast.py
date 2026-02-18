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
from typing import List, Optional

from pydantic import BaseModel, Field

# Migrated to xrtm-data
from xrtm.data.core.schemas.forecast import (
    CausalEdge,
    CausalNode,
    ForecastOutput,
    ForecastQuestion,
    MetadataBase,
)

# Migrated to xrtm-eval
from xrtm.eval.core.schemas import ForecastResolution


class TimeSeriesPoint(BaseModel):
    r"""A single point in a forecast trajectory."""

    timestamp: datetime = Field(description="The timestamp of the prediction update.")
    value: float = Field(description="The probability or value at this time.", ge=0, le=1)


class ForecastTrajectory(BaseModel):
    r"""
    The collection of probability updates over time for a single question.
    """

    question_id: str
    points: List[TimeSeriesPoint] = Field(
        default_factory=list, description="Chronological list of probability updates."
    )
    final_confidence: Optional[float] = Field(None, description="The most recent probability value.")
    rationale_history: List[str] = Field(default_factory=list, description="The evolution of reasoning over time.")


__all__ = [
    "MetadataBase",
    "ForecastQuestion",
    "CausalNode",
    "CausalEdge",
    "ForecastOutput",
    "ForecastResolution",
    "TimeSeriesPoint",
    "ForecastTrajectory",
]
