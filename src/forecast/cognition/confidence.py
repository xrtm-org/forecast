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

import logging
import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional

from forecast.schemas.base import ConfidenceMetrics

logger = logging.getLogger(__name__)


class ConfidenceStrategy(ABC):
    r"""
    Abstract base class for all confidence estimation strategies.

    Strategies define how verbal confidence and raw logprobs are synthesized
    into a final `ConfidenceMetrics` object.
    """

    @abstractmethod
    def evaluate(self, verbal: float, logprobs: Optional[List[Dict[str, Any]]]) -> ConfidenceMetrics:
        pass


class StandardHybridStrategy(ConfidenceStrategy):
    """
    Standard implementation:
    - Signal Strength = exp(mean(logprobs))
    - Hybrid = Weighted average of Verbal and Signal.
    """

    def __init__(self, verbal_weight: float = 0.3, aggregation: Literal["mean", "min", "max"] = "mean"):
        self.verbal_weight = verbal_weight
        self.aggregation = aggregation

    def evaluate(self, verbal: float, logprobs: Optional[List[Dict[str, Any]]]) -> ConfidenceMetrics:
        if not logprobs:
            return ConfidenceMetrics(verbal_confidence=verbal, hybrid_score=verbal)

        # 1. Extract values
        values = []
        for item in logprobs:
            if isinstance(item, dict):
                val = item.get("logprob")
                if val is None:
                    val = item.get("log_probability")
                if val is not None:
                    values.append(float(val))

        # 2. Aggregation Logic
        if not values:
            return ConfidenceMetrics(verbal_confidence=verbal, hybrid_score=verbal)

        if self.aggregation == "mean":
            agg_logprob = sum(values) / len(values)
        elif self.aggregation == "min":
            agg_logprob = min(values)
        elif self.aggregation == "max":
            agg_logprob = max(values)
        else:
            agg_logprob = sum(values) / len(values)

        # 3. Calculations
        try:
            signal_strength = math.exp(agg_logprob)
        except OverflowError:
            signal_strength = 0.0

        # Surprisal (negative avg logprob)
        entropy = -agg_logprob

        # 4. Hybrid Scoring
        hybrid = (verbal * self.verbal_weight) + (signal_strength * (1.0 - self.verbal_weight))
        hybrid = max(0.0, min(1.0, hybrid))

        return ConfidenceMetrics(
            verbal_confidence=verbal,
            signal_strength=signal_strength,
            entropy=entropy,
            hybrid_score=hybrid,
            aggregation_method=self.aggregation,
        )


class ConfidenceEstimator:
    """
    Standardizes how LLM 'confidence' is calculated across different models.
    """

    def __init__(self, strategy: Optional[ConfidenceStrategy] = None):
        self.strategy = strategy or StandardHybridStrategy()

    def estimate(self, verbal: float, logprobs: Optional[List[Dict[str, Any]]]) -> ConfidenceMetrics:
        return self.strategy.evaluate(verbal, logprobs)
