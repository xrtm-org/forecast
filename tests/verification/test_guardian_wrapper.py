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

import pytest

from xrtm.forecast.core.schemas.graph import TemporalContext
from xrtm.forecast.core.tools.base import Tool
from xrtm.forecast.kit.tools.guardian import GuardianTool


class UnsafeTool(Tool):
    r"""A mock tool that does NOT support Point-in-Time filtering."""

    @property
    def name(self):
        return "unsafe"

    @property
    def description(self):
        return "unsafe"

    @property
    def parameters_schema(self):
        return {}

    async def run(self, temporal_context=None, **kwargs):
        return "leaked_future_info"


class SafeTool(Tool):
    r"""A mock tool that supports Point-in-Time filtering."""

    @property
    def name(self):
        return "safe"

    @property
    def description(self):
        return "safe"

    @property
    def parameters_schema(self):
        return {}

    @property
    def pit_supported(self):
        return True

    async def run(self, temporal_context=None, **kwargs):
        return "historical_info"


@pytest.mark.asyncio
async def test_guardian_blocks_unsafe_in_strict_mode():
    unsafe = UnsafeTool()
    guardian = GuardianTool(unsafe)

    ctx = TemporalContext(reference_time=datetime(2020, 1, 1), is_backtest=True, strict_mode=True)

    with pytest.raises(RuntimeError, match="TEMPORAL VIOLATION"):
        await guardian.run(temporal_context=ctx)


@pytest.mark.asyncio
async def test_guardian_allows_unsafe_in_loose_mode():
    unsafe = UnsafeTool()
    guardian = GuardianTool(unsafe)

    # Not a backtest
    ctx_live = TemporalContext(reference_time=datetime.now(), is_backtest=False)
    assert await guardian.run(temporal_context=ctx_live) == "leaked_future_info"

    # Backtest but not strict
    ctx_loose = TemporalContext(reference_time=datetime(2020, 1, 1), is_backtest=True, strict_mode=False)
    assert await guardian.run(temporal_context=ctx_loose) == "leaked_future_info"


@pytest.mark.asyncio
async def test_guardian_allows_safe_tool():
    safe = SafeTool()
    guardian = GuardianTool(safe)

    ctx = TemporalContext(reference_time=datetime(2020, 1, 1), is_backtest=True, strict_mode=True)
    assert await guardian.run(temporal_context=ctx) == "historical_info"
