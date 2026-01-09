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

from typing import Any, List, Tuple, Union

from forecast.core.eval.definitions import EvaluationResult, Evaluator, ReliabilityBin


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
        try:
            f = float(prediction)
        except (ValueError, TypeError):
            # If not convertible, assume 0.5 (max uncertainty) or fail hard?
            # For now, let's fail hard so we know inputs are wrong
            raise ValueError(f"Prediction must be convertible to float. Got {prediction}")

        # Normalize ground truth to 0 or 1
        if isinstance(ground_truth, str):
            # Very basic string check... institutional parser would be better
            o = 1.0 if ground_truth.lower() in ["yes", "1", "true", "won", "pass"] else 0.0
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


class ExpectedCalibrationErrorEvaluator(Evaluator):
    r"""
    An evaluator that computes the Expected Calibration Error (ECE) for a set of predictions.

    ECE measures the difference between expected accuracy (confidence) and actual accuracy.
    It bins predictions (e.g., all predictions between 0.6 and 0.7) and calculates the
    absolute difference between the mean confidence and mean accuracy in each bin,
    weighted by the number of samples in the bin.

    Formula: $ECE = \sum_{b=1}^B \frac{n_b}{N} |acc(b) - conf(b)|$
    """

    def __init__(self, num_bins: int = 10):
        self.num_bins = num_bins

    def score(self, prediction: Any, ground_truth: Any) -> float:
        r"""
        ECE is a set-level metric, not meaningful for a single item.
        Returns the Brier score as a proxy for singular evaluation.
        """
        return BrierScoreEvaluator().score(prediction, ground_truth)

    def evaluate(self, prediction: Any, ground_truth: Any, subject_id: str) -> EvaluationResult:
        return BrierScoreEvaluator().evaluate(prediction, ground_truth, subject_id)

    def compute_calibration_data(self, results: List[EvaluationResult]) -> Tuple[float, List[ReliabilityBin]]:
        r"""
        Computes the global ECE score and generating reliability curve data.

        Args:
            results (`List[EvaluationResult]`):
                The list of all evaluation results to aggregate.

        Returns:
            `Tuple[float, List[ReliabilityBin]]`:
                - The scalar ECE score.
                - The list of reliability bins (for plotting).
        """
        bin_size = 1.0 / self.num_bins
        bins: List[List[EvaluationResult]] = [[] for _ in range(self.num_bins)]

        for res in results:
            try:
                # Clamp to [0, 1] just in case
                conf = min(max(float(res.prediction), 0.0), 1.0)
                # Determine bin index. Edge case: 1.0 goes to last bin.
                idx = int(conf / bin_size)
                if idx == self.num_bins:
                    idx -= 1
                bins[idx].append(res)
            except (ValueError, TypeError):
                continue

        total_count = len(results)
        ece = 0.0
        reliability_data = []

        for i, bin_items in enumerate(bins):
            n_b = len(bin_items)
            bin_center = (i + 0.5) * bin_size

            if n_b > 0:
                mean_conf = sum(float(x.prediction) for x in bin_items) / n_b

                # Mean Accuracy calculation
                accuracies = []
                for x in bin_items:
                    gt = x.ground_truth
                    normalized_gt = 0.0
                    if isinstance(gt, str):
                        normalized_gt = 1.0 if gt.lower() in ["yes", "1", "true", "won", "pass"] else 0.0
                    else:
                        normalized_gt = 1.0 if gt else 0.0
                    accuracies.append(normalized_gt)

                mean_acc = sum(accuracies) / n_b

                # ECE contribution
                ece += (n_b / total_count) * abs(mean_acc - mean_conf)

                reliability_data.append(
                    ReliabilityBin(
                        bin_center=bin_center,
                        mean_prediction=mean_conf,
                        mean_ground_truth=mean_acc,
                        count=n_b,
                    )
                )
            else:
                # Empty bin
                reliability_data.append(
                    ReliabilityBin(
                        bin_center=bin_center,
                        mean_prediction=0.0,
                        mean_ground_truth=0.0,
                        count=0,
                    )
                )

        return ece, reliability_data


__all__ = ["BrierScoreEvaluator", "ExpectedCalibrationErrorEvaluator"]
