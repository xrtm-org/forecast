from typing import Any, Union

from forecast.eval.definitions import EvaluationResult, Evaluator


class BrierScoreEvaluator(Evaluator):
    """
    Evaluator that computes the Brier Score for binary outcomes.
    Score = (forecast - outcome)^2
    Range: [0, 1]. Lower is better.
    """
    def score(self, prediction: Union[float, Any], ground_truth: Union[int, bool, str, Any]) -> float:
        """
        Calculates Brier Score.
        prediction: expected to be a float probability [0, 1].
        ground_truth: expected to be 1/True or 0/False.
        """
        # Normalize prediction
        f = float(prediction)

        # Normalize ground truth to 0 or 1
        if isinstance(ground_truth, str):
            # Very basic string check, usually handled by Resolution source
            o = 1.0 if ground_truth.lower() in ["yes", "1", "true", "won"] else 0.0
        else:
            o = 1.0 if ground_truth else 0.0

        return (f - o) ** 2

    def evaluate(self, prediction: Any, ground_truth: Any, subject_id: str) -> EvaluationResult:
        s = self.score(prediction, ground_truth)
        return EvaluationResult(
            subject_id=subject_id,
            score=s,
            ground_truth=ground_truth,
            prediction=prediction,
            metadata={"metric": "Brier Score"}
        )
