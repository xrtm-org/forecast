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

r"""Tests for cost, budget, and scheduling policies."""

from datetime import datetime, timezone

import pytest

from xrtm.forecast.core.exceptions import BudgetExceededError
from xrtm.forecast.core.policies import (
    DEEPSEEK_CNY_PRICES,
    BudgetPolicy,
    CostLedger,
    ModelPrice,
    PriceTable,
    SchedulePolicy,
    is_peak_time,
    seconds_until_off_peak,
)

OFF_PEAK = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)  # Saturday noon
PEAK = datetime(2026, 9, 28, 2, 0, tzinfo=timezone.utc)  # Monday 02:00 UTC
USAGE = {"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000, "cached_prompt_tokens": 0}


class TestScheduleHelpers:
    def test_peak_windows(self):
        assert is_peak_time(PEAK) is True
        assert is_peak_time(OFF_PEAK) is False

    def test_seconds_until_off_peak(self):
        at = datetime(2026, 9, 28, 3, 30, tzinfo=timezone.utc)
        assert seconds_until_off_peak(at) == pytest.approx(30 * 60)
        assert seconds_until_off_peak(OFF_PEAK) == 0.0

    def test_schedule_policy_toggle(self):
        policy = SchedulePolicy()
        assert policy.is_peak(PEAK) is True
        assert SchedulePolicy(enabled=False).is_peak(PEAK) is False


class TestPriceTable:
    def test_deepseek_cny_off_peak_cost(self):
        # ¥1/M input + ¥4/M output => 1M input + 1M output = ¥5
        cost = DEEPSEEK_CNY_PRICES.compute("deepseek-flash", USAGE, at=OFF_PEAK)
        assert cost == pytest.approx(5.0)

    def test_deepseek_cny_peak_is_double(self):
        cost = DEEPSEEK_CNY_PRICES.compute("deepseek-flash", USAGE, at=PEAK)
        assert cost == pytest.approx(10.0)

    def test_cached_tokens_are_cheap(self):
        usage = {"prompt_tokens": 1_000_000, "completion_tokens": 0, "cached_prompt_tokens": 1_000_000}
        cost = DEEPSEEK_CNY_PRICES.compute("deepseek-flash", usage, at=OFF_PEAK)
        assert cost == pytest.approx(0.02)

    def test_unknown_model_without_default_raises(self):
        table = PriceTable(currency="USD", prices={})
        with pytest.raises(KeyError):
            table.price_for("mystery-model")

    def test_default_price_fallback(self):
        table = PriceTable(
            currency="USD",
            default_price=ModelPrice(input_per_1m=1.0, output_per_1m=2.0),
        )
        assert table.price_for("anything").output_per_1m == 2.0


class TestCostLedgerAndBudget:
    def test_ledger_totals_and_persistence(self, tmp_path):
        path = tmp_path / "costs.jsonl"
        ledger = CostLedger(DEEPSEEK_CNY_PRICES, path=path)
        ledger.record_usage("deepseek-flash", USAGE, at=OFF_PEAK)
        ledger.record_usage("deepseek-flash", USAGE, at=OFF_PEAK)
        assert ledger.total == pytest.approx(10.0)

        reloaded = CostLedger(DEEPSEEK_CNY_PRICES, path=path)
        assert reloaded.total == pytest.approx(10.0)
        assert len(reloaded.records) == 2

    def test_daily_total_filters_by_day(self):
        ledger = CostLedger(DEEPSEEK_CNY_PRICES)
        ledger.record_usage("deepseek-flash", USAGE, at=OFF_PEAK)  # 2026-09-26
        assert ledger.daily_total("2026-09-26") == pytest.approx(5.0)
        assert ledger.daily_total("2026-09-27") == 0.0

    def test_budget_policy_limits(self):
        ledger = CostLedger(DEEPSEEK_CNY_PRICES)
        budget = BudgetPolicy(ledger, daily_limit=5.0)
        assert budget.exceeded() is False

        # Record at the current time: the daily budget window is "today", so a
        # hardcoded timestamp stops counting (and the test starts failing) as
        # soon as the clock moves past that date.
        ledger.record_usage("deepseek-flash", USAGE, at=datetime.now(timezone.utc))
        assert budget.exceeded() is True
        assert budget.remaining() == pytest.approx(0.0)
        with pytest.raises(BudgetExceededError):
            budget.check()

    def test_budget_unlimited_when_no_limits(self):
        ledger = CostLedger(DEEPSEEK_CNY_PRICES)
        budget = BudgetPolicy(ledger)
        ledger.record_usage("deepseek-flash", USAGE, at=OFF_PEAK)
        assert budget.exceeded() is False
        assert budget.remaining() is None
