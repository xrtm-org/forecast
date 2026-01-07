import os

import pytest

from examples.pipelines.custom_sentiment_workflow import run_custom_pipeline


@pytest.mark.asyncio
async def test_custom_graph_e2e(capsys):
    """
    Verifies that the custom graph example (Sentiment -> Trend) runs
    and produces the expected report output.
    """
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not found. Skipping live custom graph integration test.")

    await run_custom_pipeline()

    captured = capsys.readouterr()
    assert "--- ADVANCED CUSTOM REPORT ---" in captured.out
    assert "Detected Sentiment:" in captured.out
    assert "Trend Multiplier:" in captured.out
    assert "Explanation:" in captured.out
