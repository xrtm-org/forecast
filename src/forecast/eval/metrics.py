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

from typing import Any, Union

from forecast.eval.definitions import EvaluationResult, Evaluator


class BrierScoreEvaluator(Evaluator):
    r"""
    An evaluator that computes the Brier Score for binary outcomes.

    The Brier Score measures the accuracy of probabilistic forecasts. It is calculated as
    the mean squared difference between the predicted probability and the actual outcome.

    Formula: $BS = (f - o)^2$
    Range: [0, 1], where 0 is perfect accuracy and 1 is perfect inaccuracy.
    """

    def score(self, prediction: Union[float, Any], ground_truth: Union[int, bool, str, Any]) -> float:
        r"""
        Calculates the Brier Score for a single prediction.

        Args:
            prediction (`Union[float, Any]`):
                The predicted probability, expected to be in the range [0, 1].
            ground_truth (`Union[int, bool, str, Any]`):
                The actual outcome (1/True for occurred, 0/False for did not occur).

        Returns:
            `float`: The Brier Score.
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
        r"""
        Performs a full Brier Score evaluation.

        Args:
            prediction (`Any`):
                The forecast value.
            ground_truth (`Any`):
                The actual resolution.
            subject_id (`str`):
                Unique identifier for the item.

        Returns:
            `EvaluationResult`: The structured result.
        """
        s = self.score(prediction, ground_truth)
        return EvaluationResult(
            subject_id=subject_id,
            score=s,
            ground_truth=ground_truth,
            prediction=prediction,
            metadata={"metric": "Brier Score"},
        )


__all__ = ["BrierScoreEvaluator"]
