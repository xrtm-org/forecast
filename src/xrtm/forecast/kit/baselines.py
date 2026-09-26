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

r"""Zero-cost baseline forecasters for benchmarking.

Reference probabilities to compare LLM forecasts against — most importantly
the market's own implied probability, which is the honest benchmark for
prediction-market questions.

Example:
    >>> from xrtm.data.core.schemas.forecast import ForecastQuestion
    >>> from xrtm.forecast.kit.baselines import MarketImpliedBaseline
    >>> MarketImpliedBaseline().forecast(
    ...     ForecastQuestion(id="q", title="Will X?", context={"market_price": 0.42})
    ... )
    0.42
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, Optional, Protocol

from xrtm.data.core.schemas.forecast import ForecastQuestion

logger = logging.getLogger(__name__)

__all__ = [
    "BaselineForecaster",
    "ConstantBaseline",
    "MarketImpliedBaseline",
    "BaseRateBaseline",
]


class BaselineForecaster(Protocol):
    r"""Protocol for baseline forecasters: ``forecast(question) -> probability``."""

    def forecast(self, question: ForecastQuestion) -> float:  # pragma: no cover - protocol
        ...


def _clamp(value: Any) -> Optional[float]:
    try:
        return min(max(float(value), 0.0), 1.0)
    except (TypeError, ValueError):
        return None


class ConstantBaseline:
    r"""Always returns the same probability (default 0.5).

    Args:
        probability: The constant forecast, clamped to [0, 1].
    """

    def __init__(self, probability: float = 0.5):
        self.probability = min(max(float(probability), 0.0), 1.0)

    def forecast(self, question: ForecastQuestion) -> float:
        r"""Return the configured constant."""
        del question
        return self.probability


class MarketImpliedBaseline:
    r"""Returns the market-implied probability from the question context.

    Looks for ``context[<key>]`` first, then ``metadata.raw_data[<key>]``.
    Falls back to ``fallback`` when the value is missing or invalid.

    Args:
        key: Context/metadata key holding the market price (default ``"market_price"``).
        fallback: Value used when no usable price is present (default 0.5).
    """

    def __init__(self, key: str = "market_price", fallback: Optional[float] = 0.5):
        self.key = key
        self.fallback = fallback

    def forecast(self, question: ForecastQuestion) -> float:
        r"""Return the market-implied probability."""
        context = question.context or {}
        probability = _clamp(context.get(self.key))
        if probability is None:
            raw_data = getattr(question.metadata, "raw_data", None) or {}
            if isinstance(raw_data, dict):
                probability = _clamp(raw_data.get(self.key))
        if probability is None:
            probability = _clamp(self.fallback)
        if probability is None:
            raise ValueError(f"MarketImpliedBaseline: no usable {self.key!r} and no fallback")
        return probability


class BaseRateBaseline:
    r"""Returns the historical base rate of a set of binary outcomes.

    Args:
        outcomes: Historical outcomes on [0, 1] (empty -> ``default``).
        default: Base rate when no outcomes are provided (default 0.5).
    """

    def __init__(self, outcomes: Optional[Iterable[float]] = None, default: float = 0.5):
        values = [float(value) for value in (outcomes or []) if value is not None]
        self.rate = sum(values) / len(values) if values else min(max(float(default), 0.0), 1.0)

    def forecast(self, question: ForecastQuestion) -> float:
        r"""Return the base rate."""
        del question
        return self.rate
