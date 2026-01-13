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
from pydantic import ValidationError

from forecast.core.schemas.forecast import ForecastTrajectory, TimeSeriesPoint


def test_sentinel_trajectory_basics():
    """Verify trajectory can store points and rationale."""
    t1 = datetime(2023, 1, 1)
    t2 = datetime(2023, 1, 2)

    traj = ForecastTrajectory(
        question_id="Q1",
        points=[TimeSeriesPoint(timestamp=t1, value=0.5), TimeSeriesPoint(timestamp=t2, value=0.7)],
        rationale_history=["Uncertain", "More confident"],
    )

    assert len(traj.points) == 2
    assert traj.points[1].value == 0.7
    assert traj.question_id == "Q1"


def test_sentinel_value_constraint():
    """Verify probability must be between 0 and 1."""
    with pytest.raises(ValidationError):
        TimeSeriesPoint(timestamp=datetime.now(), value=1.5)
