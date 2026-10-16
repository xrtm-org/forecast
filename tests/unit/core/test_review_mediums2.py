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

r"""Regression tests for the second batch of Medium/Low findings.

Batch pricing, tool-argument guards, ledger bounds/timezone normalization and
the single-query web-search skill.
"""

import asyncio
import json

import pytest
from xrtm.data.core.schemas.forecast import ForecastOutput, ForecastQuestion, MetadataBase

from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.core.policies import DEEPSEEK_CNY_PRICES, CostLedger
from xrtm.forecast.kit.batch import forecast_many
from xrtm.forecast.kit.skills.web_search import WebSearchSkill
from xrtm.forecast.providers.inference.openai_provider import OpenAIProvider


class _Agent:
    async def run(self, question):
        return ForecastOutput(
            forecast_request_id=question.id,
            probability=0.6,
            reasoning="r",
            metadata=MetadataBase(source_version="test"),
        )


@pytest.mark.asyncio
async def test_forecast_many_survives_unpriced_outputs(monkeypatch, tmp_path):
    ledger = CostLedger(DEEPSEEK_CNY_PRICES, path=tmp_path / "costs.jsonl")

    def _boom(model_id, output, at=None):
        raise KeyError("no price for model")

    monkeypatch.setattr(ledger, "record_output", _boom)
    questions = [ForecastQuestion(id="q1", title="Q1"), ForecastQuestion(id="q2", title="Q2")]

    result = await forecast_many(_Agent(), questions, ledger=ledger)

    assert len(result.outputs) == 2
    assert result.errors == []


def test_cost_ledger_bounds_and_normalizes_timestamps(tmp_path):
    path = tmp_path / "costs.jsonl"
    rows = [
        {"timestamp": "2026-01-01T10:00:00", "model": "m", "cost": 1.0},  # naive -> UTC
        {"timestamp": "2026-01-01T11:00:00+00:00", "model": "m", "cost": 2.0},
        {"timestamp": "2026-01-02T09:00:00+00:00", "model": "m", "cost": 4.0},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    ledger = CostLedger(DEEPSEEK_CNY_PRICES, path=path)

    assert ledger.total == pytest.approx(7.0)
    assert ledger.daily_total("2026-01-01") == pytest.approx(3.0)
    assert ledger.daily_total("2026-01-02") == pytest.approx(4.0)
    assert ledger.records[0]["timestamp"].endswith("+00:00")


@pytest.mark.asyncio
async def test_tool_argument_errors_do_not_abort_the_turn():
    provider = OpenAIProvider(OpenAIConfig(model_id="gpt-test", api_key="fake"))

    class _Call:
        id = "c1"

        class function:
            name = "lookup"
            arguments = "{not json"

    results = await provider._execute_tool_calls([_Call()], [])

    assert results[0]["content"].startswith("Error: malformed tool arguments")


def test_web_search_skill_runs_a_single_query():
    calls = {"search": 0, "formatted": 0}

    class _Tool:
        def search(self, query, max_results=None):
            calls["search"] += 1
            return [{"title": "T", "url": "https://example.test", "content": "C"}]

        def search_formatted(self, query, max_results=None):
            calls["formatted"] += 1
            return "formatted"

    skill = WebSearchSkill(search_tool=_Tool())
    payload = asyncio.run(skill.execute("q"))

    assert calls == {"search": 1, "formatted": 0}
    assert "https://example.test" in payload["formatted"]
