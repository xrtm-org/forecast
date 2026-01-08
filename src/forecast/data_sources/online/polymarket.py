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

import logging
from typing import Any, Dict, List, Optional

import aiohttp

from forecast.data_sources.base import DataSource
from forecast.schemas.forecast import ForecastQuestion, MetadataBase

logger = logging.getLogger(__name__)


class PolymarketSource(DataSource):
    """
    DataSource implementation that fetches from the Polymarket Gamma API.
    """

    API_BASE = "https://gamma-api.polymarket.com"

    async def fetch_questions(self, query: Optional[str] = None, limit: int = 5) -> List[ForecastQuestion]:
        url = f"{self.API_BASE}/events?active=true&closed=false&limit={limit}"
        if query:
            url += f"&search={query}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.error(f"Polymarket API returned status {resp.status}")
                        return []

                    data = await resp.json()
                    questions = []
                    for item in data:
                        questions.append(self._normalize(item))
                    return questions
        except Exception as e:
            logger.error(f"Failed to fetch questions from Polymarket: {e}")
            return []

    async def get_question_by_id(self, question_id: str) -> Optional[ForecastQuestion]:
        # Implementation for single event retrieval
        url = f"{self.API_BASE}/events/{question_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return self._normalize(await resp.json())
                    return None
        except Exception as e:
            logger.error(f"Failed to retrieve Polymarket event {question_id}: {e}")
            return None

    def _normalize(self, item: Dict[str, Any]) -> ForecastQuestion:
        """
        Normalizes Polymarket Gamma API event data into a ForecastQuestion.
        """
        # Polymarket 'events' often have 'markets' inside.
        # For simplicity, we use the event title and description.
        return ForecastQuestion(
            id=str(item.get("id", "")),
            title=item.get("title", "Untitled Event"),
            content=item.get("description", ""),
            metadata=MetadataBase(
                tags=item.get("tags", []),
                market_type="binary",  # Default for demo
                source_version="polymarket-gamma-v1",
                # Pass through raw data for expert agents
                raw_data=item,
            ),
        )
