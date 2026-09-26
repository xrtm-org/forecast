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

r"""Tests for batch forecasting with budget enforcement."""

from types import SimpleNamespace

import pytest
from xrtm.data.core.schemas.forecast import ForecastOutput, ForecastQuestion, TokenUsage

from xrtm.forecast.core.policies import DEEPSEEK_CNY_PRICES, BudgetPolicy, CostLedger
from xrtm.forecast.kit.batch import forecast_many

USAGE = TokenUsage(prompt_tokens=1_000_000, completion_tokens=1_000_000)


class FakeAgent:
    def __init__(self) -> None:
        self.model = SimpleNamespace(model_id="deepseek-flash")
        self.calls = 0

    async def run(self, question: ForecastQuestion) -> ForecastOutput:
        self.calls += 1
        return ForecastOutput(
            question_id=question.id,
            probability=0.6,
            reasoning="batch test",
            usage=USAGE,
        )


def make_questions(count: int):
    return [ForecastQuestion(id=f"q{i}", title=f"Question {i}") for i in range(count)]


@pytest.mark.asyncio
async def test_forecast_many_returns_outputs_and_cost():
    agent = FakeAgent()
    ledger = CostLedger(DEEPSEEK_CNY_PRICES)

    result = await forecast_many(agent, make_questions(4), concurrency=2, ledger=ledger)

    assert len(result.outputs) == 4
    assert result.errors == []
    assert result.skipped == 0
    assert result.currency == "CNY"
    assert result.cost > 0
    assert agent.calls == 4


@pytest.mark.asyncio
async def test_forecast_many_stops_when_budget_exhausted():
    agent = FakeAgent()
    ledger = CostLedger(DEEPSEEK_CNY_PRICES)
    budget = BudgetPolicy(ledger, daily_limit=0.001)

    result = await forecast_many(agent, make_questions(4), concurrency=1, ledger=ledger, budget=budget)

    assert len(result.outputs) == 1
    assert result.skipped == 3
    assert result.cost > 0
    assert agent.calls == 1


@pytest.mark.asyncio
async def test_forecast_many_captures_errors():
    class BrokenAgent(FakeAgent):
        async def run(self, question: ForecastQuestion) -> ForecastOutput:
            raise RuntimeError("boom")

    result = await forecast_many(BrokenAgent(), make_questions(2), concurrency=2)

    assert result.outputs == []
    assert len(result.errors) == 2
    assert all("boom" in error for error in result.errors)
