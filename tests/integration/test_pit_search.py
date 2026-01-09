from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forecast.schemas.graph import TemporalContext
from forecast.tools.search import TavilySearchTool


@pytest.mark.asyncio
async def test_tavily_search_pit_integration():
    # Setup Tool
    tool = TavilySearchTool(api_key="fake")

    # Setup Historical Context
    historical = datetime(2022, 1, 1)
    context = TemporalContext(reference_time=historical, is_backtest=True)

    # Mock the post request
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"results": []})
        mock_post.return_value.__aenter__.return_value = mock_response

        await tool.run(query="Electric vehicles", temporal_context=context)

        # Verify query sent to API
        args, kwargs = mock_post.call_args
        payload = kwargs.get("json")
        assert "before:2022-01-01" in payload["query"]
        assert payload["query"] == "Electric vehicles before:2022-01-01"


@pytest.mark.asyncio
async def test_tavily_search_no_pit_outside_backtest():
    tool = TavilySearchTool(api_key="fake")

    # No backtest
    context = TemporalContext(reference_time=datetime.now(), is_backtest=False)

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"results": []})
        mock_post.return_value.__aenter__.return_value = mock_response

        await tool.run(query="Electric vehicles", temporal_context=context)

        args, kwargs = mock_post.call_args
        payload = kwargs.get("json")
        assert "before:" not in payload["query"]
        assert payload["query"] == "Electric vehicles"
