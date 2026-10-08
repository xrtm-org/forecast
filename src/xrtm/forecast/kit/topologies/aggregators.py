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
Default Aggregators for Consensus Topologies.

This module provides production-ready aggregator wrappers that implement
"Institutional Grade" statistical aggregation methods.
"""

import logging
from typing import Any, List

from xrtm.forecast.core.schemas.forecast import ForecastOutput
from xrtm.forecast.core.schemas.graph import BaseGraphState

logger = logging.getLogger(__name__)

__all__ = ["create_ivw_aggregator", "create_simple_aggregator"]


def _to_float(value: Any, default: float = 0.0) -> float:
    r"""Best-effort float conversion (``default`` on unusable input)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _output_prediction(output: Any) -> float:
    r"""Prediction from an analyst output (``confidence`` or ``probability``)."""
    value = getattr(output, "confidence", None)
    if value is None:
        value = getattr(output, "probability", None)
    return min(1.0, max(0.0, _to_float(value, 0.5)))


def _output_variance(output: Any) -> float:
    r"""Variance from an analyst output (``uncertainty``, else the 95% CI width)."""
    value = getattr(output, "uncertainty", None)
    if value is not None:
        return max(0.0, _to_float(value))
    interval = getattr(output, "confidence_interval", None)
    low = getattr(interval, "low", None)
    high = getattr(interval, "high", None)
    if low is not None and high is not None:
        # 95% interval: sd ≈ width / 3.92 → variance ≈ (width / 3.92)^2
        return ((_to_float(high) - _to_float(low)) / 3.92) ** 2
    return 0.0


def inverse_variance_weighting(outputs: List[Any]) -> tuple[float, float]:
    r"""Inverse-variance weighted mean and effective variance of *outputs*.

    Local implementation so the forecast package does not depend on
    ``xrtm-eval``: the previous cross-package import was both a layering
    violation and a signature mismatch that crashed ``use_ivw=True``.
    """
    if not outputs:
        return 0.5, 1.0
    predictions = [_output_prediction(output) for output in outputs]
    weights = []
    for output in outputs:
        variance = _output_variance(output)
        weights.append(1.0 / variance if variance > 0 else 1.0)
    total = sum(weights)
    if total <= 0:
        return sum(predictions) / len(predictions), 1.0
    mean = sum(prediction * weight for prediction, weight in zip(predictions, weights)) / total
    return mean, 1.0 / total


def create_ivw_aggregator(results_key: str = "analyst_outputs"):
    r"""
    Creates an aggregator wrapper using Inverse Variance Weighting.

    This is the recommended aggregator for production use as it gives
    lower weight to uncertain predictions.

    Args:
        results_key (`str`):
            The key in `state.context` where analyst results are stored.

    Returns:
        `Callable`: An async aggregator function compatible with `RecursiveConsensus`.

    Example:
        ```python
        >>> from xrtm.forecast.kit.topologies.aggregators import create_ivw_aggregator
        >>> consensus = RecursiveConsensus(
        ...     analyst_wrappers=[...],
        ...     aggregator_wrapper=create_ivw_aggregator(),
        ...     supervisor_wrapper=...
        ... )
        ```
    """

    async def ivw_aggregator(state: BaseGraphState, reporter: Any) -> None:
        r"""Aggregates analyst outputs using Inverse Variance Weighting."""
        results: List[dict] = state.context.get(results_key, [])

        if not results:
            state.context["aggregate"] = {"confidence": 0.5, "uncertainty": 1.0}
            logger.warning("[AGGREGATOR] No analyst outputs found")
            return None

        # Convert dicts to ForecastOutput for IVW
        outputs = []
        for r in results:
            outputs.append(
                ForecastOutput(
                    question_id=state.subject_id,
                    confidence=r.get("confidence", 0.5),
                    uncertainty=r.get("uncertainty"),
                    reasoning=r.get("reasoning", ""),
                )
            )

        mean, variance = inverse_variance_weighting(outputs)

        state.context["aggregate"] = {
            "confidence": mean,
            "uncertainty": variance,
            "method": "inverse_variance_weighting",
            "n_inputs": len(outputs),
        }

        logger.info(f"[AGGREGATOR] IVW result: {mean:.3f} (variance: {variance:.4f})")
        return None

    return ivw_aggregator


def create_simple_aggregator(results_key: str = "analyst_outputs"):
    r"""
    Creates a simple averaging aggregator (for comparison or testing).

    Args:
        results_key (`str`):
            The key in `state.context` where analyst results are stored.

    Returns:
        `Callable`: An async aggregator function compatible with `RecursiveConsensus`.
    """

    async def simple_aggregator(state: BaseGraphState, reporter: Any) -> None:
        r"""Aggregates analyst outputs using simple averaging."""
        results: List[dict] = state.context.get(results_key, [])

        if not results:
            state.context["aggregate"] = {"confidence": 0.5}
            return None

        confidences = [r.get("confidence", 0.5) for r in results]
        mean = sum(confidences) / len(confidences)

        state.context["aggregate"] = {
            "confidence": mean,
            "method": "simple_average",
            "n_inputs": len(results),
        }

        return None

    return simple_aggregator
