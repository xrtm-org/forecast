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

from freezegun import freeze_time

from forecast.core.schemas.graph import TemporalContext


def test_temporal_context_real_time():
    """Verify that is_backtest=False uses real time."""
    ctx = TemporalContext(reference_time=datetime(2020, 1, 1), is_backtest=False)
    # now() should be close to actual now, not 2020
    assert (datetime.now() - ctx.now()).total_seconds() < 1.0


def test_temporal_context_backtest_time():
    """Verify that is_backtest=True returns reference time."""
    ref = datetime(2020, 1, 1, 12, 0, 0)
    ctx = TemporalContext(reference_time=ref, is_backtest=True)
    assert ctx.now() == ref
    assert ctx.today_str == "2020-01-01"


def test_freezegun_integration():
    """Verify independent freezegun usage works."""
    ref = datetime(1999, 12, 31)
    with freeze_time(ref):
        assert datetime.now() == ref
