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

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from forecast.core.schemas.graph import BaseGraphState, TemporalContext
from forecast.core.stages.guardian import LeakageGuardian
from forecast.providers.inference.base import ModelResponse


class MockProvider:
    def __init__(self):
        self.generate_content_async = AsyncMock()


@pytest.mark.asyncio
async def test_guardian_skips_non_backtest():
    provider = MockProvider()
    guardian = LeakageGuardian(provider)
    state = BaseGraphState(subject_id="test")  # No temporal context

    report_progress = AsyncMock()
    await guardian(state, report_progress)

    provider.generate_content_async.assert_not_called()


@pytest.mark.asyncio
async def test_guardian_regex_prefilter():
    provider = MockProvider()
    guardian = LeakageGuardian(provider)

    # Text with no years > 2024
    text = "The event happened in 2023 and 2024."
    assert guardian._regex_pre_filter(text, 2024) is False

    # Text with year > 2024
    text = "In 2025, things changed."
    assert guardian._regex_pre_filter(text, 2024) is True


@pytest.mark.asyncio
async def test_guardian_redaction_flow():
    provider = MockProvider()
    provider.generate_content_async.return_value = ModelResponse(text="[REDACTED]")

    guardian = LeakageGuardian(provider)
    state = BaseGraphState(
        subject_id="test", temporal_context=TemporalContext(reference_time=datetime(2024, 1, 1), is_backtest=True)
    )
    state.node_reports["leak"] = "Something from 2025"

    report_progress = AsyncMock()
    await guardian(state, report_progress)

    assert state.node_reports["leak"] == "[REDACTED]"
    provider.generate_content_async.assert_called_once()
