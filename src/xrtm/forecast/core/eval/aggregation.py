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
Statistical Aggregation Logic for Ensembles.

This module provides "Institutional Grade" aggregation methods, moving beyond simple
averaging to weighted ensembles based on uncertainty (variance) and robust statistics.
"""

from typing import List, Tuple

from xrtm.forecast.core.schemas.forecast import ForecastOutput


def inverse_variance_weighting(
    predictions: List[ForecastOutput], default_variance: float = 0.05
) -> Tuple[float, float]:
    r"""
    Aggregates predictions using Inverse Variance Weighting (IVW).

    Formula:
        weights_i = 1 / (variance_i + epsilon)
        y_hat = sum(weights_i * y_i) / sum(weights_i)
        combined_variance = 1 / sum(weights_i)

    Args:
        predictions: List of forecast outputs.
        default_variance: Variance to assume if an agent doesn't provide one.

    Returns:
        Tuple[float, float]: (Weighted Mean Confidence, Combined Variance)
    """
    if not predictions:
        return 0.5, 1.0  # Maximum uncertainty

    values = []
    weights = []

    for p in predictions:
        val = p.confidence

        # Prefer explicit uncertainty if provided
        if p.uncertainty is not None:
            variance = p.uncertainty
        else:
            # Heuristic fallback: Conviction proxy.
            # High conviction (near 0 or 1) implies low variance.
            dist = abs(val - 0.5) * 2  # 0..1 scale (0=uncertain, 1=certain)
            # Invert conviction to get variance proxy.
            variance = 0.25 * (1.0 - dist) + 0.01

        # Prevent division by zero
        weight = 1.0 / max(variance, 0.01)
        values.append(val)
        weights.append(weight)

    sum_weights = sum(weights)
    if sum_weights == 0:
        return 0.5, 1.0

    weighted_mean = sum(v * w for v, w in zip(values, weights)) / sum_weights
    combined_variance = 1.0 / sum_weights

    return weighted_mean, combined_variance


def robustness_check_mad(values: List[float], threat_level: float = 2.0) -> List[float]:
    r"""
    Filter out outliers using Median Absolute Deviation (MAD).

    Args:
        values: List of float scores.
        threat_level: How many MADs away to consider an outlier (default 2.0).

    Returns:
        List[float]: The filtered list of values (outliers removed).
    """
    if len(values) < 3:
        return values

    median = sorted(values)[len(values) // 2]
    deviations = [abs(x - median) for x in values]
    mad = sorted(deviations)[len(deviations) // 2]

    if mad == 0:
        return values

    return [x for x in values if abs(x - median) <= threat_level * mad]
