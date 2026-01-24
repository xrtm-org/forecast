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

from xrtm.forecast.core.eval.aggregation import inverse_variance_weighting, robustness_check_mad
from xrtm.forecast.core.schemas.forecast import ForecastOutput


def test_ivw_basic():
    # Two identical agents -> average
    p1 = ForecastOutput(question_id="q1", confidence=0.8, reasoning="A")
    p2 = ForecastOutput(question_id="q1", confidence=0.8, reasoning="B")
    mean, var = inverse_variance_weighting([p1, p2])
    assert mean == pytest.approx(0.8)


def test_ivw_weighted():
    # Agent A: 0.9 (Specific, high conviction -> low variance)
    # Agent B: 0.5 (Unsure -> high variance)
    # Result should be pulled closer to 0.9 than 0.5
    p1 = ForecastOutput(question_id="q1", confidence=0.9, reasoning="Sure")
    p2 = ForecastOutput(question_id="q1", confidence=0.5, reasoning="Unsure")

    mean, _ = inverse_variance_weighting([p1, p2])

    # Simple average would be 0.7
    # Weighted average should be > 0.7 because 0.9 is 'lower variance' in our heuristic
    assert mean > 0.75


def test_mad_outlier():
    # 0.1, 0.1, 0.1, 0.9 (0.9 is outlier)
    values = [0.1, 0.1, 0.12, 0.9]
    filtered = robustness_check_mad(values, threat_level=2.0)
    assert 0.9 not in filtered
    assert len(filtered) == 3
