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

r"""Unit tests for WaybackTool."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forecast.providers.tools.wayback import WaybackResult, WaybackTool


class TestWaybackResult:
    r"""Test WaybackResult dataclass."""

    def test_create_result(self):
        r"""Create a WaybackResult."""
        result = WaybackResult(
            url="https://example.com",
            archived_url="https://web.archive.org/web/20220101/https://example.com",
            timestamp=datetime(2022, 1, 1),
            status_code=200,
        )
        assert result.url == "https://example.com"
        assert result.status_code == 200
        assert result.content is None

    def test_result_with_content(self):
        r"""Result with content."""
        result = WaybackResult(
            url="https://example.com",
            archived_url="https://web.archive.org/web/20220101/https://example.com",
            timestamp=datetime(2022, 1, 1),
            status_code=200,
            content="Hello world",
        )
        assert result.content == "Hello world"


class TestWaybackToolBasics:
    r"""Test WaybackTool basic properties."""

    def test_tool_attributes(self):
        r"""Tool has correct attributes."""
        tool = WaybackTool()
        assert tool.name == "wayback"
        assert tool.pit_supported is True
        assert "Archive" in tool.description

    def test_timeout_configurable(self):
        r"""Timeout is configurable."""
        tool = WaybackTool(timeout=60.0)
        assert tool.timeout == 60.0


class TestWaybackToolCheckAvailability:
    r"""Test check_availability method."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_snapshot(self):
        r"""Returns None when no snapshot available."""
        tool = WaybackTool()

        with patch.object(tool, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"archived_snapshots": {}}
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_client

            result = await tool.check_availability(
                "https://example.com",
                datetime(2023, 1, 1),
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_result_when_snapshot_exists(self):
        r"""Returns result when snapshot exists."""
        tool = WaybackTool()

        with patch.object(tool, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "archived_snapshots": {
                    "closest": {
                        "url": "https://web.archive.org/web/20220615/...",
                        "timestamp": "20220615120000",
                        "status": "200",
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_client

            result = await tool.check_availability(
                "https://example.com",
                datetime(2023, 1, 1),
            )
            assert result is not None
            assert result.status_code == 200
            assert result.timestamp.year == 2022

    @pytest.mark.asyncio
    async def test_rejects_snapshot_after_target_date(self):
        r"""Rejects snapshot archived after target date."""
        tool = WaybackTool()

        with patch.object(tool, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "archived_snapshots": {
                    "closest": {
                        "url": "https://web.archive.org/web/20230615/...",
                        "timestamp": "20230615120000",  # After target
                        "status": "200",
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_client

            result = await tool.check_availability(
                "https://example.com",
                datetime(2023, 1, 1),  # Target date before snapshot
            )
            assert result is None  # Should reject


class TestWaybackToolRun:
    r"""Test run method."""

    @pytest.mark.asyncio
    async def test_run_returns_list(self):
        r"""Run returns list of dicts."""
        tool = WaybackTool()

        with patch.object(tool, "search_cdx") as mock_search:
            mock_search.return_value = [
                WaybackResult(
                    url="https://example.com/article1",
                    archived_url="https://web.archive.org/...",
                    timestamp=datetime(2022, 6, 15),
                    status_code=200,
                ),
            ]

            results = await tool.run(query="example.com", before_date=datetime(2023, 1, 1))

            assert len(results) == 1
            assert results[0]["url"] == "https://example.com/article1"
            assert "timestamp" in results[0]
