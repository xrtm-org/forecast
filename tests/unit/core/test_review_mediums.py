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

r"""Regression tests for the 2026-10-08 Medium findings.

Graph timeouts are enforced, the temporal context is UTC-aware, and cache
failures degrade to misses instead of breaking successful calls.
"""

import asyncio
from datetime import datetime

import pytest

from xrtm.forecast.core.cache import InferenceCache
from xrtm.forecast.core.config.graph import GraphConfig
from xrtm.forecast.core.exceptions import GraphTimeoutError
from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.schemas.graph import BaseGraphState, TemporalContext


@pytest.mark.asyncio
async def test_graph_timeout_is_enforced():
    async def slow_node(state, report):
        await asyncio.sleep(5)
        return None

    orch = Orchestrator(GraphConfig(timeout=0.05))
    orch.add_node("slow", slow_node)
    orch.set_entry_point("slow")

    with pytest.raises(GraphTimeoutError):
        await orch.run(BaseGraphState(subject_id="s"))


@pytest.mark.asyncio
async def test_graph_without_timeout_completes():
    async def quick_node(state, report):
        state.node_reports["done"] = True
        return None

    orch = Orchestrator(GraphConfig())
    orch.add_node("quick", quick_node)
    orch.set_entry_point("quick")

    state = await orch.run(BaseGraphState(subject_id="s"))
    assert state.node_reports["done"] is True


def test_temporal_context_now_is_timezone_aware():
    context = TemporalContext(reference_time=datetime(2026, 1, 1))
    assert context.now().tzinfo is not None


def test_cache_failures_degrade_to_misses(tmp_path, monkeypatch):
    cache = InferenceCache(db_path=str(tmp_path / "cache.db"), ttl_seconds=60)
    cache.set("k", "v")
    assert cache.get("k") == "v"

    class _Broken:
        def execute(self, *args, **kwargs):
            raise RuntimeError("sqlite exploded")

    monkeypatch.setattr(cache, "_conn", _Broken())
    assert cache.get("k") is None  # a miss, not an exception
    cache.set("k2", "v2")  # must not raise
