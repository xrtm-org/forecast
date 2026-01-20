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

import time
from datetime import datetime

import pytest

from forecast import AsyncRuntime
from forecast.core.epistemics import IntegrityGuardian, SourceTrustRegistry
from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.forecast import ForecastOutput
from forecast.core.schemas.graph import BaseGraphState, TemporalContext
from forecast.kit.eval.epistemic_evaluator import EpistemicEvaluator


@pytest.mark.asyncio
async def test_chronos_sleep_backtest_acceleration():
    r"""Verifies that AsyncRuntime.sleep is bypassed in backtest mode."""

    # Setup state with backtest context
    state = BaseGraphState(
        subject_id="sleep-test", temporal_context=TemporalContext(reference_time=datetime.now(), is_backtest=True)
    )

    orch = Orchestrator()

    async def fast_stage(s, on_progress=None):
        start = time.time()
        # We sleep for 10 seconds of "virtual" time
        await AsyncRuntime.sleep(10.0)
        end = time.time()
        return {"elapsed": end - start}

    orch.add_node("fast_stage", fast_stage)
    orch.set_entry_point("fast_stage")

    start_total = time.time()
    await orch.run(state)
    end_total = time.time()

    # Even though we slept for 10s, it should have finished in milliseconds
    elapsed = state.node_reports["fast_stage"]["elapsed"]
    total_elapsed = end_total - start_total

    print(f"DEBUG: Virtual sleep 10s took {elapsed:.4f}s real time.")
    assert elapsed < 0.1, f"Sleep was not bypassed! Took {elapsed:.2f}s"
    assert total_elapsed < 0.2


@pytest.mark.asyncio
async def test_epistemic_security_validation():
    r"""Verifies that the Epistemic Security layer correctly flags sources."""

    registry = SourceTrustRegistry(default_trust=0.5)
    registry.register_source("reputable.org", 0.9, tags=["verified"])
    registry.register_source("shady-news.com", 0.1, tags=["unverified"])

    guardian = IntegrityGuardian(registry, threshold=0.3)

    sources = ["reputable.org", "shady-news.com", "unknown.net"]
    results = await guardian.validate_data_sources(sources)

    assert "reputable.org" in results["passed"]
    assert "shady-news.com" in results["blocked"]
    assert "unknown.net" in results["passed"]  # Default 0.5 > 0.3 threshold

    # Test Evaluator
    evaluator = EpistemicEvaluator(registry)
    output = ForecastOutput(
        question_id="test",
        confidence=0.8,
        reasoning="Because of news...",
        metadata={"sources": ["reputable.org", "shady-news.com"]},
    )

    report = await evaluator.evaluate_forecast_integrity(output)
    assert report["aggregate_trust_score"] == 0.5  # (0.9 + 0.1) / 2
    assert report["integrity_level"] == "MEDIUM"
    assert "shady-news.com" in report["source_validation"]["blocked"]
