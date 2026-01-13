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

import numpy as np

from forecast.core.eval.calibration import PlattScaler
from forecast.core.eval.definitions import EvaluationResult
from forecast.kit.eval.metrics import BrierScoreEvaluator


class TestPlattScaler:
    r"""Unit tests for the PlattScaler."""

    def test_identity_scaling(self):
        """
        Verify that perfectly calibrated data results in near-identity scaling parameters.
        a approx 1, b approx 0.
        """
        # Generate synthetic perfectly calibrated data
        # Prob 0.2 -> 20% positives
        # Prob 0.8 -> 80% positives
        np.random.seed(42)
        n_samples = 1000
        y_probs = []
        y_true = []

        for p in [0.2, 0.5, 0.8]:
            n = int(n_samples / 3)
            outcomes = np.random.binomial(1, p, n)
            y_probs.extend([p] * n)
            y_true.extend(outcomes)

        scaler = PlattScaler()
        scaler.fit(y_true, y_probs)

        assert scaler.fitted
        # Tolerances for convergence
        assert 0.8 < scaler.a < 1.2
        assert -0.2 < scaler.b < 0.2

        # Test transform
        t = scaler.transform(0.5)
        assert 0.45 < t < 0.55

    def test_bias_correction(self):
        """
        Verify that under-confident data (everything is 0.5) gets pushed to extremes
        if the reality determines it.
        Actually, let's test a simple shift.
        Model says 0.3, Reality is 0.6.
        """
        # Model consistently underestimates
        y_probs = [0.3] * 1000
        # Reality is 60% positive
        y_true = np.random.binomial(1, 0.6, 1000).tolist()

        scaler = PlattScaler()
        scaler.fit(y_true, y_probs)

        # Transform 0.3 should be closer to 0.6
        calibrated = scaler.transform(0.3)
        assert calibrated > 0.45

    def test_save_load(self, tmp_path):
        scaler = PlattScaler(a=2.5, b=-0.5, fitted=True)
        p = tmp_path / "scaler.pkl"
        scaler.save(p)

        loaded = PlattScaler().load(p)
        assert loaded.a == 2.5
        assert loaded.b == -0.5
        assert loaded.fitted


class TestBrierDecomposition:
    r"""Unit tests for Brier Score decomposition."""

    def test_decomposition_identity(self):
        """
        Verify that BS = Rel - Res + Unc
        """
        # Create a small set of results
        # 2 bins: 0.2 (0/5 pos), 0.8 (4/5 pos)
        results = []

        # Bin 1: Pred=0.2, Outcome=0 (5 times)
        for _ in range(5):
            results.append(EvaluationResult(subject_id="x", score=0.0, ground_truth=0, prediction=0.2))

        # Bin 2: Pred=0.8, Outcome=1 (4 times), Outcome=0 (1 time)
        for _ in range(4):
            results.append(EvaluationResult(subject_id="x", score=0.0, ground_truth=1, prediction=0.8))
        results.append(EvaluationResult(subject_id="x", score=0.0, ground_truth=0, prediction=0.8))

        evaluator = BrierScoreEvaluator()
        decomp = evaluator.compute_decomposition(results, num_bins=10)  # 10 bins is standard, our preds fall nicely

        # Expected calculation:
        # N = 10
        # Outcomes: 0,0,0,0,0, 1,1,1,1,0 -> Total 4 positives. o_bar = 0.4.
        # Uncertainty = 0.4 * 0.6 = 0.24

        assert abs(decomp.uncertainty - 0.24) < 1e-5

        # Check identity
        # We need to manually calc BS average
        bs_sum = 0
        for r in results:
            bs_sum += (r.prediction - r.ground_truth) ** 2
        bs_mean = bs_sum / 10

        assert abs(decomp.score - (decomp.reliability - decomp.resolution + decomp.uncertainty)) < 1e-5
        assert abs(decomp.score - bs_mean) < 1e-5
