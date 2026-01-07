import os

import pytest

from examples.external_tools import main as run_external_tools_example


@pytest.mark.asyncio
async def test_external_tools_e2e(capsys):
    """
    Verifies the external tool integration example handshake.
    Note: Requires GEMINI_API_KEY for a real LLM run,
    otherwise skips with a message.
    """
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not found. Skipping live LLM integration test.")

    await run_external_tools_example()

    captured = capsys.readouterr()
    assert "FINAL AGENT REPORT (Using External Strand Tool):" in captured.out
    assert "[App] Ingesting external tool: get_market_sentiment" in captured.out
