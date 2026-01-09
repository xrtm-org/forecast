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

from forecast.kit.cognition.confidence import ConfidenceEstimator, StandardHybridStrategy


def test_confidence_hybrid_strategy():
    r"""
    Verifies the hybrid confidence strategy combining verbal scores and signal strength.
    """
    strategy = StandardHybridStrategy(verbal_weight=0.5)

    # Test case 1: High verbal, High logprob (approx 0) -> High hybrid
    # logprob 0 -> signal 1.0. verbal 1.0. hybrid = 0.5*1 + 0.5*1 = 1.0
    metrics = strategy.evaluate(verbal=1.0, logprobs=[{"logprob": 0.0}])
    assert metrics.hybrid_score == 1.0
    assert metrics.signal_strength == 1.0

    # Test case 2: Low verbal, Low logprob (-100) -> Low hybrid
    # logprob -100 -> signal ~0. verbal 0. hybrid = 0.
    metrics = strategy.evaluate(verbal=0.0, logprobs=[{"logprob": -100.0}])
    assert metrics.hybrid_score == pytest.approx(0.0, abs=0.01)


def test_confidence_aggregation_modes():
    r"""
    Verifies that mean, min, and max aggregation modes operate correctly on logprobs.
    """
    logprobs = [{"logprob": -1.0}, {"logprob": -3.0}]

    # Mean: -2.0 -> exp(-2) ~= 0.135
    strategy = StandardHybridStrategy(aggregation="mean")
    metrics = strategy.evaluate(verbal=0.5, logprobs=logprobs)
    expected_signal = 0.135335
    assert metrics.signal_strength == pytest.approx(expected_signal, abs=0.001)

    # Min: -3.0 -> exp(-3) ~= 0.049
    strategy = StandardHybridStrategy(aggregation="min")
    metrics = strategy.evaluate(verbal=0.5, logprobs=logprobs)
    expected_signal = 0.049787
    assert metrics.signal_strength == pytest.approx(expected_signal, abs=0.001)


def test_confidence_estimator_defaults():
    r"""
    Verifies that the ConfidenceEstimator provides sensible defaults without custom strategies.
    """
    estimator = ConfidenceEstimator()
    metrics = estimator.estimate(verbal=1.0, logprobs=[])
    # Defaults: verbal_weight=0.3. If no logprobs, returns verbal as hybrid
    assert metrics.hybrid_score == 1.0
