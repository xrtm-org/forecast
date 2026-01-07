from typing import Any, Dict, List, Protocol

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """
    Standard output for a single evaluation.
    """
    subject_id: str
    score: float
    ground_truth: Any
    prediction: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Evaluator(Protocol):
    """
    Protocol for scoring a prediction against ground truth.
    """
    def score(self, prediction: Any, ground_truth: Any) -> float:
        """
        Computes the numerical score.
        """
        ...

    def evaluate(self, prediction: Any, ground_truth: Any, subject_id: str) -> EvaluationResult:
        """
        Performs a full evaluation and returns a structured result.
        """
        ...

class EvaluationReport(BaseModel):
    """
    Aggregate report for a series of evaluations.
    """
    metric_name: str
    mean_score: float
    total_evaluations: int
    results: List[EvaluationResult] = Field(default_factory=list)
    summary_statistics: Dict[str, float] = Field(default_factory=dict)
