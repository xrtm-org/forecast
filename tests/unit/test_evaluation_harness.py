import pytest

from forecast.eval.definitions import EvaluationResult
from forecast.eval.metrics import BrierScoreEvaluator


def test_brier_score_calc():
    evaluator = BrierScoreEvaluator()

    # Perfect guess
    assert evaluator.score(1.0, 1) == 0.0
    assert evaluator.score(0.0, 0) == 0.0

    # Worst guess
    assert evaluator.score(1.0, 0) == 1.0
    assert evaluator.score(0.0, 1) == 1.0

    # Middle guess
    # (0.7 - 1)^2 = (-0.3)^2 = 0.09
    assert pytest.approx(evaluator.score(0.7, 1)) == 0.09

    # String truth
    assert evaluator.score(1.0, "yes") == 0.0
    assert evaluator.score(1.0, "won") == 0.0

def test_brier_evaluate_output():
    evaluator = BrierScoreEvaluator()
    res = evaluator.evaluate(prediction=0.8, ground_truth=1, subject_id="test_q")

    assert isinstance(res, EvaluationResult)
    assert res.subject_id == "test_q"
    assert res.score == pytest.approx(0.04)
    assert res.prediction == 0.8
