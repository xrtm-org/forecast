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

r"""Wayback Machine tool for temporally-verified content retrieval.

This module provides a Tool implementation that retrieves content from the
Internet Archive (Wayback Machine) for temporal integrity verification.
Content is only returned if it was archived before the specified date,
providing physics-based proof of temporal existence.

Example:
    >>> from forecast.providers.tools.wayback import WaybackTool
    >>> from datetime import datetime
    >>> tool = WaybackTool()
    >>> # results = await tool.run("AI news", before_date=datetime(2023, 1, 1))
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from forecast.core.tools.base import Tool

__all__ = ["WaybackTool", "WaybackResult"]

logger = logging.getLogger(__name__)

WAYBACK_API_URL = "https://archive.org/wayback/available"
WAYBACK_CDX_URL = "https://web.archive.org/cdx/search/cdx"


@dataclass
class WaybackResult:
    r"""Result from Wayback Machine query.

    Args:
        url (`str`):
            Original URL that was archived.
        archived_url (`str`):
            Full URL to the archived snapshot.
        timestamp (`datetime`):
            When the content was archived.
        status_code (`int`):
            HTTP status code at time of archiving.
        content (`str`, *optional*):
            Extracted text content if retrieved.

    Example:
        >>> result = WaybackResult(
        ...     url="https://example.com",
        ...     archived_url="https://web.archive.org/web/20220101/...",
        ...     timestamp=datetime(2022, 1, 1),
        ...     status_code=200
        ... )
    """

    url: str
    archived_url: str
    timestamp: datetime
    status_code: int
    content: Optional[str] = None


class WaybackTool(Tool):
    r"""Tool for retrieving temporally-verified content from Archive.org.

    This tool provides zero-leakage temporal verification by only returning
    content that was archived before the specified date. This ensures that
    backtests cannot be contaminated by future information.

    Args:
        timeout (`float`, *optional*, defaults to `30.0`):
            Request timeout in seconds.

    Attributes:
        name (`str`): Tool identifier ("wayback").
        description (`str`): Tool description for agent consumption.
        pit_supported (`bool`): Always True - this tool is inherently PiT safe.

    Example:
        >>> tool = WaybackTool()
        >>> tool.pit_supported
        True
    """

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        r"""The unique identifier of the tool."""
        return "wayback"

    @property
    def description(self) -> str:
        r"""A descriptive summary of the tool's purpose and usage."""
        return "Search Internet Archive for content archived before a specific date."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        r"""Returns a JSON schema representing the tool's arguments."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "URL or URL pattern to search in the archive.",
                },
                "before_date": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Only return content archived before this date (ISO format).",
                },
            },
            "required": ["query"],
        }

    @property
    def pit_supported(self) -> bool:
        r"""Whether this tool supports Point-in-Time (historical) filtering."""
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        r"""Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def check_availability(self, url: str, before_date: datetime) -> Optional[WaybackResult]:
        r"""Check if a URL has an archived snapshot before the given date.

        Args:
            url (`str`):
                The URL to check.
            before_date (`datetime`):
                Only return snapshots archived before this date.

        Returns:
            `Optional[WaybackResult]`: The archived snapshot info, or None if not found.

        Example:
            >>> import asyncio
            >>> tool = WaybackTool()
            >>> # result = asyncio.run(tool.check_availability(
            >>> #     "https://example.com", datetime(2023, 1, 1)
            >>> # ))
        """
        client = await self._get_client()
        timestamp = before_date.strftime("%Y%m%d")

        try:
            response = await client.get(
                WAYBACK_API_URL,
                params={"url": url, "timestamp": timestamp},
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("archived_snapshots", {}).get("closest"):
                logger.debug("No snapshot found for %s before %s", url, before_date)
                return None

            snapshot = data["archived_snapshots"]["closest"]
            snap_timestamp = datetime.strptime(snapshot["timestamp"], "%Y%m%d%H%M%S")

            # Verify snapshot is actually before the target date
            if snap_timestamp >= before_date:
                logger.debug(
                    "Snapshot %s is after target date %s",
                    snap_timestamp,
                    before_date,
                )
                return None

            return WaybackResult(
                url=url,
                archived_url=snapshot["url"],
                timestamp=snap_timestamp,
                status_code=int(snapshot.get("status", 200)),
            )

        except httpx.HTTPError as e:
            logger.warning("Wayback API error for %s: %s", url, e)
            return None

    async def search_cdx(
        self,
        query: str,
        before_date: datetime,
        limit: int = 10,
    ) -> List[WaybackResult]:
        r"""Search the CDX index for archived URLs matching a query.

        Args:
            query (`str`):
                Search query (domain or URL pattern).
            before_date (`datetime`):
                Only return snapshots archived before this date.
            limit (`int`, *optional*, defaults to `10`):
                Maximum number of results.

        Returns:
            `List[WaybackResult]`: List of matching archived snapshots.

        Example:
            >>> import asyncio
            >>> tool = WaybackTool()
            >>> # results = asyncio.run(tool.search_cdx(
            >>> #     "reuters.com/*ai*", datetime(2023, 1, 1)
            >>> # ))
        """
        client = await self._get_client()
        to_date = before_date.strftime("%Y%m%d")

        try:
            response = await client.get(
                WAYBACK_CDX_URL,
                params={
                    "url": query,
                    "output": "json",
                    "to": to_date,
                    "limit": limit,
                    "fl": "original,timestamp,statuscode",
                },
            )
            response.raise_for_status()
            data = response.json()

            if len(data) <= 1:  # First row is headers
                return []

            results = []
            for row in data[1:]:  # Skip header row
                try:
                    original_url, timestamp, status = row[0], row[1], row[2]
                    snap_timestamp = datetime.strptime(timestamp, "%Y%m%d%H%M%S")

                    if snap_timestamp >= before_date:
                        continue

                    archived_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                    results.append(
                        WaybackResult(
                            url=original_url,
                            archived_url=archived_url,
                            timestamp=snap_timestamp,
                            status_code=int(status) if status else 200,
                        )
                    )
                except (ValueError, IndexError) as e:
                    logger.debug("Error parsing CDX row: %s", e)
                    continue

            return results

        except httpx.HTTPError as e:
            logger.warning("CDX search error for %s: %s", query, e)
            return []

    async def run(
        self,
        temporal_context: Optional[Any] = None,
        query: str = "",
        before_date: Optional[datetime] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        r"""Execute the Wayback search tool.

        Args:
            temporal_context (`Optional[TemporalContext]`, *optional*):
                Metadata for temporal sandboxing (reference time, etc.).
            query (`str`):
                URL or URL pattern to search.
            before_date (`datetime`, *optional*):
                Only return content archived before this date.
                If not provided, uses temporal_context or current time.
            **kwargs:
                Additional arguments (for Tool interface compatibility).

        Returns:
            `List[Dict[str, Any]]`: List of result dictionaries.

        Example:
            >>> import asyncio
            >>> tool = WaybackTool()
            >>> # results = asyncio.run(tool.run(query="example.com"))
        """
        # Determine the effective before_date
        if before_date is None:
            if temporal_context is not None and hasattr(temporal_context, "reference_time"):
                before_date = temporal_context.reference_time
            else:
                before_date = datetime.now(timezone.utc)

        results = await self.search_cdx(query, before_date)

        return [
            {
                "url": r.url,
                "archived_url": r.archived_url,
                "timestamp": r.timestamp.isoformat(),
                "status_code": r.status_code,
            }
            for r in results
        ]

    async def close(self) -> None:
        r"""Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
