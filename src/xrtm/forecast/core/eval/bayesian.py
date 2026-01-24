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
Core mathematical utilities for Bayesian forecasting.
Focuses on Bayes Factor (Likelihood Ratio) updates.
r"""

import logging

logger = logging.getLogger(__name__)


def probability_to_odds(probability: float) -> float:
    r"""
    Converts a probability [0, 1] to odds [0, inf).

    Args:
        probability (`float`): The probability value.

    Returns:
        `float`: The odds value.
    r"""
    if probability >= 1.0:
        return float("inf")
    if probability <= 0.0:
        return 0.0
    return probability / (1.0 - probability)


def odds_to_probability(odds: float) -> float:
    r"""
    Converts odds [0, inf) to probability [0, 1].

    Args:
        odds (`float`): The odds value.

    Returns:
        `float`: The probability value.
    r"""
    if odds == float("inf"):
        return 1.0
    return odds / (1.0 + odds)


def bayesian_update(prior_probability: float, bayes_factor: float) -> float:
    r"""
    Performs a Bayesian update using a Bayes Factor (Likelihood Ratio).

    Posterior Odds = Prior Odds * Bayes Factor

    Args:
        prior_probability (`float`): The prior probability [0, 1].
        bayes_factor (`float`): The Bayes Factor (Likelihood Ratio).
            BF > 1 supports the hypothesis, BF < 1 supports the alternative.

    Returns:
        `float`: The posterior probability [0, 1].

    Example:
        >>> bayesian_update(0.2, 1.5)
        0.2727272727272727
    r"""
    prior_odds = probability_to_odds(prior_probability)
    posterior_odds = prior_odds * bayes_factor
    return odds_to_probability(posterior_odds)


__all__ = ["probability_to_odds", "odds_to_probability", "bayesian_update"]
