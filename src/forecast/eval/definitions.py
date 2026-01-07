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

from typing import Any, Dict, List, Protocol

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    r"""
    A structured container for the outcome of a single evaluation event.

    Attributes:
        subject_id (`str`):
            The identifier of the item being evaluated (e.g., a question ID).
        score (`float`):
            The numerical score assigned by the evaluator.
        ground_truth (`Any`):
            The known-correct value or resolution outcome.
        prediction (`Any`):
            The value produced by the agent/model.
        metadata (`Dict[str, Any]`):
            Additional context about the evaluation (e.g., timestamp, version).
    """

    subject_id: str
    score: float
    ground_truth: Any
    prediction: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Evaluator(Protocol):
    r"""
    A structural protocol defining how to score agent predictions against ground truth.

    Implementations of this protocol provide the mathematical or logical basis
    for assessing forecast quality.
    """

    def score(self, prediction: Any, ground_truth: Any) -> float:
        r"""
        Computes a numerical score for a prediction.

        Args:
            prediction (`Any`):
                The value to be assessed.
            ground_truth (`Any`):
                The reference value to compare against.

        Returns:
            `float`: The calculated score.
        """
        ...

    def evaluate(self, prediction: Any, ground_truth: Any, subject_id: str) -> EvaluationResult:
        r"""
        Performs a complete evaluation and returns a structured result.

        Args:
            prediction (`Any`):
                The value to be assessed.
            ground_truth (`Any`):
                The reference value to compare against.
            subject_id (`str`):
                The identifier for the item being evaluated.

        Returns:
            `EvaluationResult`: A structured container for the evaluation details.
        """
        ...


class EvaluationReport(BaseModel):
    r"""
    An aggregate report summarizing the performance across multiple evaluations.

    Attributes:
        metric_name (`str`):
            The name of the metric used (e.g., "Brier Score").
        mean_score (`float`):
            The average score across all evaluations.
        total_evaluations (`int`):
            The number of items evaluated.
        results (`List[EvaluationResult]`):
            The individual evaluation records.
        summary_statistics (`Dict[str, float]`):
            Additional stats like variance, median, or quartiles.
    """

    metric_name: str
    mean_score: float
    total_evaluations: int
    results: List[EvaluationResult] = Field(default_factory=list)
    summary_statistics: Dict[str, float] = Field(default_factory=dict)


__all__ = ["EvaluationResult", "Evaluator", "EvaluationReport"]
