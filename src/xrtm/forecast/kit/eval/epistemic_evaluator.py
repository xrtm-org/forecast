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
from typing import Any, Dict, Optional

from xrtm.forecast.core.epistemics import IntegrityGuardian, SourceTrustRegistry
from xrtm.forecast.core.schemas.forecast import ForecastOutput

logger = logging.getLogger(__name__)

__all__ = ["EpistemicEvaluator"]


class EpistemicEvaluator:
    r"""
    A kit component for auditing the 'Epistemic Security' of a forecast.
    Analyzes the sources used in a reasoning chain and computes a trust score.
    """

    def __init__(self, registry: Optional[SourceTrustRegistry] = None):
        r"""
        Initializes the evaluator with a trust registry.

        Args:
            registry (`SourceTrustRegistry`, *optional*):
                The source trust registry to use. If not provided, a new empty one is created.

        Example:
            ```python
            >>> evaluator = EpistemicEvaluator(registry)
            ```
        """
        self.registry = registry or SourceTrustRegistry()
        self.guardian = IntegrityGuardian(self.registry)

    async def evaluate_forecast_integrity(self, output: ForecastOutput) -> Dict[str, Any]:
        r"""
        Analyzes the sources referenced in a ForecastOutput's reasoning or metadata.

        Args:
            output (`ForecastOutput`):
                The forecast output to audit.

        Returns:
            `Dict[str, Any]`:
                A report containing the aggregate trust score, source validation results,
                and an overall integrity level ("HIGH", "MEDIUM", "LOW").

        Example:
            ```python
            >>> evaluator = EpistemicEvaluator(registry)
            >>> report = await evaluator.evaluate_forecast_integrity(forecast_output)
            >>> print(report["integrity_level"])
            'HIGH'
            ```
        """
        # In a real implementation, we would extract domains from 'reasoning'
        # or from a specific 'sources' field in metadata.
        sources = output.metadata.get("sources", [])

        # Also check logical_trace for explicit source mentions if possible
        # For simplicity, we assume 'sources' are listed in metadata

        validation = await self.guardian.validate_data_sources(sources)

        # Compute aggregate trust
        scores = [self.registry.get_trust_score(s) for s in sources]
        avg_trust = sum(scores) / len(scores) if scores else 0.5

        return {
            "aggregate_trust_score": avg_trust,
            "source_validation": validation,
            "integrity_level": "HIGH" if avg_trust > 0.8 else "MEDIUM" if avg_trust >= 0.5 else "LOW",
        }
