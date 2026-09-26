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

r"""Decision schemas for typed decision providers.

System-One style models (e.g. TypeSafe Jev) return a choice from a predefined
option set with probabilities instead of generating free-form text. These
schemas standardize that contract so routers can mix decision models and LLMs.
"""

from typing import Dict

from pydantic import BaseModel, Field

__all__ = ["DecisionOption", "DecisionResult"]


class DecisionOption(BaseModel):
    r"""One selectable option in a decision.

    Attributes:
        name: Machine-readable option identifier.
        description: Human-readable explanation of the option.
    """

    name: str = Field(..., description="Machine-readable option identifier")
    description: str = Field(default="", description="Human-readable explanation of the option")


class DecisionResult(BaseModel):
    r"""The outcome of a typed decision.

    Attributes:
        decision: The chosen option name.
        confidence: Confidence in the chosen option (0-1).
        probabilities: Probability assigned to each option (normalized when available).
        escalate: Whether the provider recommends escalating to a stronger model.
        escalated: Whether an escalation router actually escalated this decision.
        rationale: Short explanation for the decision.
        usage: Token usage for this decision, if the provider reports it.
    """

    decision: str = Field(..., description="The chosen option name")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in the chosen option")
    probabilities: Dict[str, float] = Field(
        default_factory=dict,
        description="Probability assigned to each option",
    )
    escalate: bool = Field(
        default=False,
        description="Whether the provider recommends escalating to a stronger model",
    )
    escalated: bool = Field(
        default=False,
        description="Whether an escalation router actually escalated this decision",
    )
    rationale: str = Field(default="", description="Short explanation for the decision")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage for this decision, if available")
