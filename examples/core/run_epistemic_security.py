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

import asyncio

from forecast.core.epistemics import IntegrityGuardian, SourceTrustRegistry
from forecast.core.schemas.forecast import ForecastOutput
from forecast.kit.eval.epistemic_evaluator import EpistemicEvaluator


async def run_epistemic_demo():
    r"""Demonstrates the Epistemic Security layer filtering and evaluation."""
    print("--- [EPISTEMIC SECURITY DEMO] ---")

    # 1. Setup Trust Registry
    registry = SourceTrustRegistry(default_trust=0.5)
    registry.register_source("peer-reviewed-science.org", 1.0, tags=["official"])
    registry.register_source("sensational-tabloid.com", 0.1, tags=["unverified"])
    print("Registered sources in registry.")

    # 2. Automated Filtering (IntegrityGuardian)
    guardian = IntegrityGuardian(registry, threshold=0.4)
    sources = ["peer-reviewed-science.org", "sensational-tabloid.com", "unknown-blog.net"]
    results = await guardian.validate_data_sources(sources)

    print("\nGuardian Validation Results:")
    print(f"  Passed:  {results['passed']}")
    print(f"  Flagged: {results['flagged']}")
    print(f"  Blocked: {results['blocked']}")

    # 3. Post-Analysis (EpistemicEvaluator)
    evaluator = EpistemicEvaluator(registry)
    output = ForecastOutput(
        question_id="demo-123",
        confidence=0.85,
        reasoning="Based on recent findings...",
        metadata={"sources": ["peer-reviewed-science.org", "sensational-tabloid.com"]},
    )

    report = await evaluator.evaluate_forecast_integrity(output)
    print("\nFinal Forecast Integrity Report:")
    print(f"  Aggregate Trust: {report['aggregate_trust_score']:.2f}")
    print(f"  Integrity Level: {report['integrity_level']}")


if __name__ == "__main__":
    asyncio.run(run_epistemic_demo())
