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

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union

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
    r"""

    subject_id: str
    score: float
    ground_truth: Any
    prediction: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReliabilityBin(BaseModel):
    r"""
    Data structure for a single bin in a reliability diagram.

    Attributes:
        bin_center (`float`): The center of the confidence bin (e.g., 0.05 for [0.0, 0.1]).
        mean_prediction (`float`): Average predicted confidence in this bin.
        mean_ground_truth (`float`): Average actual outcome (accuracy) in this bin.
        count (`int`): Number of predictions falling into this bin.
    r"""

    bin_center: float
    mean_prediction: float
    mean_ground_truth: float
    count: int


class BrierDecomposition(BaseModel):
    r"""
    The three-component decomposition of the Brier Score.

    BS = Reliability - Resolution + Uncertainty

    Attributes:
        reliability (`float`): Measures calibration (lower is better).
        resolution (`float`): Measures ability to distinguish outcomes (higher is better).
        uncertainty (`float`): The uncertainty of the environment (base rate varience).
        score (`float`): The total Brier Score.
    """

    reliability: float
    resolution: float
    uncertainty: float
    score: float


class Evaluator(Protocol):
    r"""
    A structural protocol defining how to score agent predictions against ground truth.

    Implementations of this protocol provide the mathematical or logical basis
    for assessing forecast quality.
    r"""

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
        r"""
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
        r"""
        ...


class EvaluationReport(BaseModel):
    r"""
    A unified summary container for a collection of evaluation results.

    Aggregates individual scores into a high-level performance metric and
    optionally provides calibration data (reliability bins).

    Attributes:
        metric_name (`str`):
            The name of the metric used (e.g., "Brier Score", "Accuracy").
        mean_score (`float`):
            The average score across all results in this report.
        total_evaluations (`int`):
            The number of items evaluated.
        results (`list[EvaluationResult]`):
            The raw list of individual evaluation outcomes.
        summary_statistics (`dict[str, Any]`, *optional*):
            Additional metrics (e.g., ECE score, variance).
        reliability_bins (`list[ReliabilityBin]`, *optional*):
            Data for calibration analysis (e.g., reliability diagrams).

    Example:
        ```python
        from forecast.core.eval.definitions import EvaluationReport, EvaluationResult

        res = EvaluationResult(subject_id="q1", score=0.0, ground_truth=1, prediction=1.0)
        report = EvaluationReport(
            metric_name="Exact Match",
            mean_score=1.0,
            total_evaluations=1,
            results=[res]
        )
        print(report.model_dump_json(indent=2))
        ```
    r"""

    metric_name: str
    mean_score: float
    total_evaluations: int
    results: List[EvaluationResult] = Field(default_factory=list)
    summary_statistics: Dict[str, float] = Field(default_factory=dict)
    reliability_bins: Optional[List[ReliabilityBin]] = None
    slices: Optional[Dict[str, "EvaluationReport"]] = Field(
        default=None, description="Sub-reports grouped by metadata tags"
    )

    def to_json(self, path: Union[str, Path]) -> None:
        r"""
        Exports the report to a JSON file.
        r"""
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))

    def to_pandas(self) -> Any:
        r"""
        Converts results to a pandas DataFrame (if pandas is installed).
        Returns a DataFrame or raises ImportError.
        r"""
        try:
            import pandas as pd

            return pd.DataFrame([r.model_dump() for r in self.results])
        except ImportError:
            raise ImportError("Pandas is required for to_pandas(). Install it with `pip install pandas`.")


__all__ = ["EvaluationResult", "Evaluator", "EvaluationReport", "ReliabilityBin", "BrierDecomposition"]
