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

r"""
Sentinel Driver Base Interface.

Defines the abstract contract for dynamic forecasting drivers that track
how forecasts evolve over time.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

from forecast.core.schemas.forecast import ForecastQuestion, ForecastTrajectory


class TriggerRules(BaseModel):
    r"""
    Configuration for when a forecast should be updated.

    Attributes:
        interval (`timedelta`):
            The minimum time between update checks.
        keywords (`List[str]`, *optional*):
            Keywords to search for in news/events.
        max_updates (`int`, *optional*):
            Maximum number of updates before stopping.
    """

    interval: timedelta = Field(default=timedelta(hours=1))
    keywords: List[str] = Field(default_factory=list)
    max_updates: Optional[int] = Field(default=None)


class WatchedQuestion(BaseModel):
    r"""
    Internal representation of a question being monitored by the Sentinel.

    Attributes:
        question (`ForecastQuestion`):
            The question being tracked.
        rules (`TriggerRules`):
            The update rules for this question.
        trajectory (`ForecastTrajectory`):
            The accumulated trajectory of probability updates.
        last_checked (`datetime`):
            When the question was last evaluated for updates.
        update_count (`int`):
            Number of updates performed so far.
    """

    question: ForecastQuestion
    rules: TriggerRules
    trajectory: ForecastTrajectory
    last_checked: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    update_count: int = 0


class SentinelDriver(ABC):
    r"""
    Abstract base class for Sentinel drivers.

    A Sentinel driver manages the lifecycle of dynamic forecasts, determining
    when to check for new information and how to update probability estimates.

    Example:
        ```python
        >>> driver = PollingDriver(agent=my_agent, interval=3600)
        >>> await driver.register_watch(question, rules)
        >>> await driver.run()  # Starts the polling loop
        ```
    """

    @abstractmethod
    async def register_watch(
        self,
        question: ForecastQuestion,
        rules: TriggerRules,
        initial_confidence: Optional[float] = None,
    ) -> str:
        r"""
        Registers a question for dynamic tracking.

        Args:
            question (`ForecastQuestion`):
                The question to track.
            rules (`TriggerRules`):
                The rules governing update frequency and triggers.
            initial_confidence (`float`, *optional*):
                Starting probability estimate.

        Returns:
            `str`: A watch ID that can be used to reference this watch.
        """
        pass

    @abstractmethod
    async def unregister_watch(self, watch_id: str) -> bool:
        r"""
        Stops tracking a question.

        Args:
            watch_id (`str`):
                The ID returned by `register_watch`.

        Returns:
            `bool`: True if successfully unregistered.
        """
        pass

    @abstractmethod
    async def get_trajectory(self, watch_id: str) -> Optional[ForecastTrajectory]:
        r"""
        Retrieves the current trajectory for a watched question.

        Args:
            watch_id (`str`):
                The ID returned by `register_watch`.

        Returns:
            `ForecastTrajectory` | None: The trajectory, or None if not found.
        """
        pass

    @abstractmethod
    async def run_once(self) -> int:
        r"""
        Performs a single update cycle across all watched questions.

        Returns:
            `int`: The number of questions that were updated.
        """
        pass

    @abstractmethod
    async def run(self, max_cycles: Optional[int] = None) -> None:
        r"""
        Starts the continuous monitoring loop.

        Args:
            max_cycles (`int`, *optional*):
                Maximum number of cycles before stopping. None = infinite.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        r"""
        Gracefully stops the monitoring loop.
        """
        pass


__all__ = [
    "TriggerRules",
    "WatchedQuestion",
    "SentinelDriver",
]
