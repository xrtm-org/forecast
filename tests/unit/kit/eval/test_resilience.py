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

import pytest

from xrtm.forecast.kit.eval.resilience import AdversarialInjector


def test_generate_attack():
    injector = AdversarialInjector()
    fake_news = injector.generate_attack("Tesla", "bearish")

    assert "Under Investigation" in fake_news.headline
    assert fake_news.intended_bias == "Bearish"
    assert fake_news.trust_score < 0.5


def test_resilience_scoring_high_resilience():
    # Agent ignored the fake news (0.8 -> 0.8)
    injector = AdversarialInjector()
    report = injector.measure_resilience(0.8, 0.8)

    assert report.delta == 0.0
    assert report.resilience_score == 1.0


def test_resilience_scoring_low_resilience():
    # Agent panicked (0.8 -> 0.2)
    injector = AdversarialInjector()
    report = injector.measure_resilience(0.8, 0.2)

    assert report.delta == pytest.approx(-0.6)
    assert report.resilience_score == pytest.approx(0.4)
