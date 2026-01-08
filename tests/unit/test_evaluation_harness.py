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

import pytest

from forecast.eval.definitions import EvaluationResult
from forecast.eval.metrics import BrierScoreEvaluator


def test_brier_score_calc():
    r"""
    Verifies the mathematical correctness of Brier score calculations.
    """
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
    r"""
    Verifies that the Brier evaluator returns a properly structured EvaluationResult.
    """
    evaluator = BrierScoreEvaluator()
    res = evaluator.evaluate(prediction=0.8, ground_truth=1, subject_id="test_q")

    assert isinstance(res, EvaluationResult)
    assert res.subject_id == "test_q"
    assert res.score == pytest.approx(0.04)
    assert res.prediction == 0.8
