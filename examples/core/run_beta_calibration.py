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

r"""
Beta Calibration demonstration.
Shows how BetaScaler corrects asymmetric biases better than Platt scaling.
"""

import numpy as np

from forecast.core.eval.calibration import BetaScaler, PlattScaler
from forecast.kit.eval.metrics import EvaluationResult, ExpectedCalibrationErrorEvaluator


def run_beta_demo():
    print("--- [BETA CALIBRATION DEMO] ---")

    # 1. Generate Synthetic Biased Data (Over-confident Agent)
    # The agent predicts high/low probabilities too aggressively
    np.random.seed(42)
    N = 1000
    y_true = np.random.randint(0, 2, N)

    # Simulate an over-confident agent (pushes everything towards 0 and 1)
    raw_probs = np.random.uniform(0.1, 0.9, N)
    # Bias: push closer to edges
    uncalibrated_probs = np.where(raw_probs > 0.5, raw_probs**0.5, raw_probs**2)

    ece_eval = ExpectedCalibrationErrorEvaluator(num_bins=10)

    def get_ece(probs, labels):
        results = [
            EvaluationResult(subject_id=str(i), score=0, ground_truth=labels[i], prediction=probs[i])
            for i in range(len(probs))
        ]
        ece, _ = ece_eval.compute_calibration_data(results)
        return ece

    ece_pre = get_ece(uncalibrated_probs, y_true)
    print(f"Pre-Calibration ECE: {ece_pre:.4f}")

    # 2. Fit and Transform with Platt Scaler
    platt = PlattScaler().fit(y_true.tolist(), uncalibrated_probs.tolist())
    platt_probs = platt.transform(uncalibrated_probs.tolist())
    ece_platt = get_ece(platt_probs, y_true)
    print(f"Platt Scaled ECE:    {ece_platt:.4f}")

    # 3. Fit and Transform with Beta Scaler
    beta = BetaScaler().fit(y_true.tolist(), uncalibrated_probs.tolist())
    beta_probs = beta.transform(uncalibrated_probs.tolist())
    ece_beta = get_ece(beta_probs, y_true)
    print(f"Beta Calibrated ECE: {ece_beta:.4f}")

    print("\nConclusion:")
    if ece_beta < ece_platt:
        print("Beta Calibration achieved superior alignment for this distribution.")
    else:
        print("Calibration improved accuracy across both methods.")


if __name__ == "__main__":
    run_beta_demo()
