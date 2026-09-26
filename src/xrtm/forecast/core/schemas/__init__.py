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

r"""Framework schemas — runtime state, forecast types, workflow blueprints, and decisions."""

from xrtm.forecast.core.schemas.decision import DecisionOption, DecisionResult
from xrtm.forecast.core.schemas.prompt import PromptTemplate
from xrtm.forecast.core.schemas.workflow import (
    WORKFLOW_SCHEMA_VERSION,
    ArtifactPolicy,
    ConditionalRouteSpec,
    EdgeSpec,
    GraphSpec,
    NodeSpec,
    ParallelGroupSpec,
    QuestionSourceSpec,
    RuntimeProfileSpec,
    ScoringPolicy,
    WorkflowBlueprint,
    WorkflowSummary,
)

__all__ = [
    "WORKFLOW_SCHEMA_VERSION",
    "ArtifactPolicy",
    "ConditionalRouteSpec",
    "DecisionOption",
    "DecisionResult",
    "PromptTemplate",
    "EdgeSpec",
    "GraphSpec",
    "NodeSpec",
    "ParallelGroupSpec",
    "QuestionSourceSpec",
    "RuntimeProfileSpec",
    "ScoringPolicy",
    "WorkflowBlueprint",
    "WorkflowSummary",
]
