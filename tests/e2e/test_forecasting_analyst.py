import os

import pytest
from pydantic import SecretStr

from forecast.agents.specialists.analyst import ForecastingAnalyst
from forecast.data_sources.local import LocalDataSource
from forecast.inference.config import GeminiConfig
from forecast.inference.factory import ModelFactory
from forecast.pipelines.analyst import GenericAnalystPipeline


@pytest.mark.asyncio
async def test_analyst_pipeline_e2e():
    """
    Validates the full v0.1.0 pipeline flow using local data.
    """
    # 1. Setup (Mock-like setup but using real provider if key exists, otherwise we'd need mocks)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not found")

    config = GeminiConfig(
        model_id="gemini-2.0-flash-lite",
        api_key=SecretStr(api_key)
    )
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
