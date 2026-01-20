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

r"""Unit tests for the Sentinel PollingDriver."""

from datetime import timedelta

import pytest

from forecast.core.schemas.forecast import ForecastQuestion
from forecast.kit.sentinel import PollingDriver, TriggerRules


class MockInferenceProvider:
    r"""Mock provider for testing."""

    def __init__(self) -> None:
        self.call_count = 0

    async def generate(self, prompt: str) -> "MockResponse":
        self.call_count += 1
        return MockResponse(f"NEW_PROBABILITY: 0.65\nREASONING: Test update #{self.call_count}")


class MockResponse:
    def __init__(self, text: str) -> None:
        self.text = text


@pytest.fixture
def mock_model() -> MockInferenceProvider:
    return MockInferenceProvider()


@pytest.fixture
def sample_question() -> ForecastQuestion:
    return ForecastQuestion(
        id="test_question_1",
        title="Will event X occur?",
        content="Test question for sentinel protocol.",
    )


@pytest.fixture
def trigger_rules() -> TriggerRules:
    return TriggerRules(
        interval=timedelta(seconds=0),  # Immediate updates for testing
        max_updates=3,
    )


class TestPollingDriver:
    r"""Tests for PollingDriver functionality."""

    @pytest.mark.asyncio
    async def test_register_watch(
        self,
        mock_model: MockInferenceProvider,
        sample_question: ForecastQuestion,
        trigger_rules: TriggerRules,
    ) -> None:
        r"""Test that questions can be registered for watching."""
        driver = PollingDriver(model=mock_model)  # type: ignore

        watch_id = await driver.register_watch(
            question=sample_question,
            rules=trigger_rules,
            initial_confidence=0.5,
        )

        assert watch_id is not None
        assert len(watch_id) > 0

        trajectory = await driver.get_trajectory(watch_id)
        assert trajectory is not None
        assert trajectory.question_id == sample_question.id
        assert trajectory.final_confidence == 0.5
        assert len(trajectory.points) == 1

    @pytest.mark.asyncio
    async def test_unregister_watch(
        self,
        mock_model: MockInferenceProvider,
        sample_question: ForecastQuestion,
        trigger_rules: TriggerRules,
    ) -> None:
        r"""Test that watches can be unregistered."""
        driver = PollingDriver(model=mock_model)  # type: ignore

        watch_id = await driver.register_watch(
            question=sample_question,
            rules=trigger_rules,
            initial_confidence=0.5,
        )

        result = await driver.unregister_watch(watch_id)
        assert result is True

        trajectory = await driver.get_trajectory(watch_id)
        assert trajectory is None

    @pytest.mark.asyncio
    async def test_run_once_updates_trajectory(
        self,
        mock_model: MockInferenceProvider,
        sample_question: ForecastQuestion,
        trigger_rules: TriggerRules,
    ) -> None:
        r"""Test that run_once updates the trajectory."""
        driver = PollingDriver(model=mock_model)  # type: ignore

        watch_id = await driver.register_watch(
            question=sample_question,
            rules=trigger_rules,
            initial_confidence=0.5,
        )

        # Run one update cycle
        updated_count = await driver.run_once()
        assert updated_count == 1

        trajectory = await driver.get_trajectory(watch_id)
        assert trajectory is not None
        assert len(trajectory.points) == 2  # Initial + 1 update
        assert trajectory.final_confidence == 0.65  # From mock

    @pytest.mark.asyncio
    async def test_max_updates_respected(
        self,
        mock_model: MockInferenceProvider,
        sample_question: ForecastQuestion,
        trigger_rules: TriggerRules,
    ) -> None:
        r"""Test that max_updates limit is respected."""
        driver = PollingDriver(model=mock_model)  # type: ignore

        watch_id = await driver.register_watch(
            question=sample_question,
            rules=trigger_rules,  # max_updates=3
            initial_confidence=0.5,
        )

        # Run 5 cycles - should only update 3 times
        for _ in range(5):
            await driver.run_once()

        trajectory = await driver.get_trajectory(watch_id)
        assert trajectory is not None
        # Initial point + 3 updates = 4 points
        assert len(trajectory.points) == 4
        assert mock_model.call_count == 3
