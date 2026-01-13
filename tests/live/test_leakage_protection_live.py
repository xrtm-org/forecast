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

import os
from datetime import datetime

import pytest
from pydantic import SecretStr

from forecast.core.config.inference import GeminiConfig, OpenAIConfig
from forecast.core.schemas.graph import BaseGraphState, TemporalContext
from forecast.core.stages.guardian import LeakageGuardian
from forecast.providers.inference.factory import ModelFactory


@pytest.mark.live
@pytest.mark.asyncio
async def test_leakage_guardian_live_openai():
    r"""Verifies the LeakageGuardian with a live OpenAI model."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set")

    config = OpenAIConfig(model_id="gpt-4o-mini", api_key=SecretStr(key))
    provider = ModelFactory.get_provider(config)
    guardian = LeakageGuardian(provider=provider)

    # Historical Context (Mid-2024)
    ref_time = datetime(2024, 6, 15)
    state = BaseGraphState(
        subject_id="live_guardian_test", temporal_context=TemporalContext(reference_time=ref_time, is_backtest=True)
    )

    # Inject information that refers to 2025 (Future)
    state.node_reports["search"] = (
        "In May 2024, OpenAI announced GPT-4o. "
        "Looking ahead, the 2025 global tech summit will feature new AI breakthroughs."
    )

    # Run Guardian
    async def mock_progress(p, s, st, msg):
        pass

    await guardian(state, mock_progress)

    # Check that 2025 info was redacted
    print(f"\n[LIVE TEST] Post-Guardian Report: {state.node_reports['search']}")
    # The LLM should follow instructions and replace the 2025 sentence.
    assert "[REDACTED_FUTURE_LEAK]" in state.node_reports["search"]
    assert "2025" not in state.node_reports["search"]


@pytest.mark.live
@pytest.mark.asyncio
async def test_leakage_guardian_live_gemini():
    r"""Verifies the LeakageGuardian with a live Gemini model."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        pytest.skip("GEMINI_API_KEY not set")

    config = GeminiConfig(model_id="gemini-2.0-flash-lite", api_key=SecretStr(key))
    provider = ModelFactory.get_provider(config)
    guardian = LeakageGuardian(provider=provider)

    ref_time = datetime(2023, 1, 1)
    state = BaseGraphState(
        subject_id="live_guardian_test_gemini",
        temporal_context=TemporalContext(reference_time=ref_time, is_backtest=True),
    )

    state.node_reports["news"] = "The 2022 World Cup was in Qatar. The 2024 Olympics will be in Paris."

    async def mock_progress(p, s, st, msg):
        pass

    await guardian(state, mock_progress)

    print(f"\n[LIVE TEST] Gemini Post-Guardian: {state.node_reports['news']}")
    assert "2024" not in state.node_reports["news"]
    assert "[REDACTED_FUTURE_LEAK]" in state.node_reports["news"]
