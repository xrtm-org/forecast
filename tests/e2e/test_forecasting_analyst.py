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

import pytest
from pydantic import SecretStr

from forecast.core.config.inference import GeminiConfig
from forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from forecast.kit.pipelines.analyst import GenericAnalystPipeline
from forecast.providers.data.local import LocalDataSource
from forecast.providers.inference.factory import ModelFactory


@pytest.mark.asyncio
async def test_analyst_pipeline_e2e():
    """
    Validates the full v0.1.0 pipeline flow using local data.
    """
    # 1. Setup (Mock-like setup but using real provider if key exists, otherwise we'd need mocks)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not found")

    config = GeminiConfig(model_id="gemini-2.0-flash-lite", api_key=SecretStr(api_key))
    provider = ModelFactory.get_provider(config)

    data_source = LocalDataSource("examples/data/polymarket_sample.json")
    analyst = ForecastingAnalyst(model=provider)
    pipeline = GenericAnalystPipeline(data_source=data_source, analyst=analyst)

    # 2. Run
    target_id = "eth-ath-2026"
    state = await pipeline.run(subject_id=target_id)

    # 3. Assertions
    assert "output" in state.context
    assert "report" in state.context

    output = state.context["output"]
    assert output.question_id == target_id
    assert 0 <= output.confidence <= 1
    assert len(output.logical_trace) > 0

    # Verify Double-Trace
    assert "ingestion" in state.execution_path
    assert "analysis" in state.execution_path

    # Verify Report content
    report = state.context["report"]
    assert "# Forecast Execution Report" in report
    assert "Structural Trace" in report
    assert "Logical Trace" in report
    assert f"**{state.execution_path[-1]}**" in report
