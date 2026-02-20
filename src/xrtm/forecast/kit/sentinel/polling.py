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
Polling-based Sentinel Driver.

Implements the "Delta Function" pattern (Option C from Sentinel Protocol):
periodic, stateless check-ins that update forecasts based on new information.

This is the recommended default driver as it works out-of-the-box without
external infrastructure (no Redis, no Kafka).
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from xrtm.forecast.core.interfaces import InferenceProvider
from xrtm.forecast.core.schemas.forecast import ForecastQuestion, ForecastTrajectory, TimeSeriesPoint
from xrtm.forecast.kit.sentinel.base import SentinelDriver, TriggerRules, WatchedQuestion

logger = logging.getLogger(__name__)


class PollingDriver(SentinelDriver):
    r"""
    A polling-based Sentinel driver for dynamic forecasting.

    The PollingDriver periodically checks all watched questions and updates
    their probability estimates when new information is available. It uses
    a delta prompt approach to minimize token costs.

    Attributes:
        model (`InferenceProvider`):
            The LLM provider for generating probability updates.
        search_fn (`Callable`, *optional*):
            A function that searches for new information given keywords and a date.
        default_interval (`float`):
            Default seconds between poll cycles (3600 = 1 hour).

    Example:
        ```python
        >>> driver = PollingDriver(model=my_llm, default_interval=3600)
        >>> watch_id = await driver.register_watch(question, rules)
        >>> await driver.run(max_cycles=10)  # Run 10 update cycles
        >>> trajectory = await driver.get_trajectory(watch_id)
        ```
    """

    def __init__(
        self,
        model: InferenceProvider,
        search_fn: Optional[Callable[..., Any]] = None,
        default_interval: float = 3600.0,
    ) -> None:
        r"""
        Initializes the PollingDriver.

        Args:
            model (`InferenceProvider`):
                The inference provider for delta updates.
            search_fn (`Callable`, *optional*):
                Custom search function for finding new information.
            default_interval (`float`):
                Default polling interval in seconds.
        """
        self.model = model
        self.search_fn = search_fn
        self.default_interval = default_interval
        self._watches: Dict[str, WatchedQuestion] = {}
        self._running = False
        self._stop_event: Optional[asyncio.Event] = None

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
                The rules governing update frequency.
            initial_confidence (`float`, *optional*):
                Starting probability estimate. If not provided, will generate one.

        Returns:
            `str`: A unique watch ID.
        """
        watch_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Create initial trajectory
        trajectory = ForecastTrajectory(
            question_id=question.id,
            points=[],
            final_confidence=initial_confidence,
            rationale_history=[],
        )

        # If initial confidence provided, add first point
        if initial_confidence is not None:
            trajectory.points.append(TimeSeriesPoint(timestamp=now, value=initial_confidence))

        watched = WatchedQuestion(
            question=question,
            rules=rules,
            trajectory=trajectory,
            last_checked=now,
            update_count=0,
        )

        self._watches[watch_id] = watched
        logger.info(f"[SENTINEL] Registered watch {watch_id} for question '{question.id}'")
        return watch_id

    async def unregister_watch(self, watch_id: str) -> bool:
        r"""
        Stops tracking a question.

        Args:
            watch_id (`str`):
                The watch ID to remove.

        Returns:
            `bool`: True if successfully removed.
        """
        if watch_id in self._watches:
            del self._watches[watch_id]
            logger.info(f"[SENTINEL] Unregistered watch {watch_id}")
            return True
        return False

    async def get_trajectory(self, watch_id: str) -> Optional[ForecastTrajectory]:
        r"""
        Retrieves the trajectory for a watched question.

        Args:
            watch_id (`str`):
                The watch ID.

        Returns:
            `ForecastTrajectory` | None: The trajectory if found.
        """
        watched = self._watches.get(watch_id)
        return watched.trajectory if watched else None

    async def _should_update(self, watched: WatchedQuestion) -> bool:
        r"""Determines if a watched question should be updated."""
        now = datetime.now(timezone.utc)
        time_since_check = now - watched.last_checked

        # Check interval
        if time_since_check < watched.rules.interval:
            return False

        # Check max updates
        if watched.rules.max_updates is not None:
            if watched.update_count >= watched.rules.max_updates:
                return False

        return True

    async def _perform_delta_update(self, watched: WatchedQuestion) -> Optional[Tuple[float, str]]:
        r"""
        Performs a delta update using the Bayesian update prompt.

        Args:
            watched (`WatchedQuestion`):
                The question to update.

        Returns:
            `Tuple[float, str]` | None: The new probability and reasoning, or None if failed.
        """
        question = watched.question
        trajectory = watched.trajectory
        current_confidence = trajectory.final_confidence or 0.5

        # Build the delta prompt
        prompt = f"""You are a Bayesian forecaster updating your probability estimate.

QUESTION: {question.title}

PREVIOUS ESTIMATE: {current_confidence:.1%}

PREVIOUS REASONING:
{trajectory.rationale_history[-1] if trajectory.rationale_history else "Initial estimate."}

TASK: Consider if any new developments might have occurred since your last update.
Update your probability estimate if warranted.

Respond in this exact format:
NEW_PROBABILITY: <float between 0 and 1>
REASONING: <brief explanation of any change>
"""

        try:
            response = await self.model.generate(prompt)
            text = response.text

            # Parse response
            new_prob = current_confidence
            reasoning = ""

            for line in text.split("\n"):
                if line.startswith("NEW_PROBABILITY:"):
                    try:
                        new_prob = float(line.split(":")[1].strip())
                        new_prob = max(0.0, min(1.0, new_prob))
                    except (ValueError, IndexError):
                        pass
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()

            return new_prob, reasoning

        except Exception as e:
            logger.error(f"[SENTINEL] Delta update failed: {e}")
            return None

    async def run_once(self) -> int:
        r"""
        Performs a single update cycle across all watched questions.

        Returns:
            `int`: Number of questions updated.
        """
        updated_count = 0
        now = datetime.now(timezone.utc)

        update_tasks = []
        pending_watches = []

        for watch_id, watched in list(self._watches.items()):
            if not await self._should_update(watched):
                continue

            logger.debug(f"[SENTINEL] Checking {watch_id} for updates...")
            update_tasks.append(self._perform_delta_update(watched))
            pending_watches.append((watch_id, watched))

        if not update_tasks:
            results = []
        else:
            results = await asyncio.gather(*update_tasks)

        for (watch_id, watched), result in zip(pending_watches, results):
            if result is not None:
                new_prob, reasoning = result

                # Update trajectory
                watched.trajectory.points.append(TimeSeriesPoint(timestamp=now, value=new_prob))
                watched.trajectory.final_confidence = new_prob
                if reasoning:
                    watched.trajectory.rationale_history.append(reasoning)

                watched.last_checked = now
                watched.update_count += 1
                updated_count += 1

                logger.info(f"[SENTINEL] Updated {watch_id}: {new_prob:.1%} (update #{watched.update_count})")

        return updated_count

    async def run(self, max_cycles: Optional[int] = None) -> None:
        r"""
        Starts the continuous monitoring loop.

        Args:
            max_cycles (`int`, *optional*):
                Maximum cycles before stopping. None = infinite.
        """
        self._running = True
        self._stop_event = asyncio.Event()
        cycle_count = 0

        logger.info(f"[SENTINEL] Starting polling loop (interval={self.default_interval}s)")

        while self._running:
            if max_cycles is not None and cycle_count >= max_cycles:
                logger.info(f"[SENTINEL] Reached max cycles ({max_cycles})")
                break

            updated = await self.run_once()
            cycle_count += 1

            logger.debug(f"[SENTINEL] Cycle {cycle_count} complete. Updated {updated}/{len(self._watches)} questions.")

            # Wait for interval or stop signal
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.default_interval,
                )
                # Stop event was set
                break
            except asyncio.TimeoutError:
                # Normal timeout, continue loop
                pass

        self._running = False
        logger.info("[SENTINEL] Polling loop stopped")

    async def stop(self) -> None:
        r"""Gracefully stops the monitoring loop."""
        self._running = False
        if self._stop_event:
            self._stop_event.set()
        logger.info("[SENTINEL] Stop requested")


__all__ = ["PollingDriver"]
