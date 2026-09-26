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

r"""Tests for baseline forecasters."""

import pytest
from xrtm.data.core.schemas.forecast import ForecastQuestion, MetadataBase

from xrtm.forecast.kit.baselines import BaseRateBaseline, ConstantBaseline, MarketImpliedBaseline


def _question(**context):
    return ForecastQuestion(id="q1", title="Will X happen?", context=context or None)


def test_constant_baseline_clamps():
    assert ConstantBaseline(1.5).forecast(_question()) == 1.0
    assert ConstantBaseline(-0.2).forecast(_question()) == 0.0


def test_market_implied_reads_context():
    assert MarketImpliedBaseline().forecast(_question(market_price=0.42)) == 0.42


def test_market_implied_falls_back_to_metadata():
    question = ForecastQuestion(
        id="q2",
        title="Will Y?",
        metadata=MetadataBase(raw_data={"market_price": 0.7}),
    )
    assert MarketImpliedBaseline().forecast(question) == 0.7


def test_market_implied_fallback_when_missing():
    assert MarketImpliedBaseline().forecast(_question()) == 0.5


def test_market_implied_without_fallback_raises():
    with pytest.raises(ValueError):
        MarketImpliedBaseline(fallback=None).forecast(_question())


def test_base_rate_from_outcomes():
    baseline = BaseRateBaseline([1.0, 0.0, 1.0, 1.0])
    assert baseline.forecast(_question()) == pytest.approx(0.75)
    assert BaseRateBaseline().forecast(_question()) == 0.5
