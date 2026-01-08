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

import os
import sqlite3

import pytest

from forecast.tools.data import PandasSkill, SQLSkill


@pytest.fixture
def temp_db():
    db_file = "test_qa_data.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE inventory (id INTEGER, item TEXT, count INTEGER)")
    conn.execute("INSERT INTO inventory VALUES (1, 'Widget', 10), (2, 'Gadget', 5)")
    conn.commit()
    conn.close()

    yield db_file

    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.mark.asyncio
async def test_sql_skill_hardened_security(temp_db):
    r"""Verifies that SQLSkill enforces read-only guardrails."""
    skill = SQLSkill(db_url=temp_db)

    # 1. Successful SELECT
    res = await skill.run(query="SELECT item, count FROM inventory WHERE count > 7")
    assert len(res) == 1
    assert res[0]["item"] == "Widget"

    # 2. Blocked DROP
    res = await skill.run(query="DROP TABLE inventory")
    assert "Error" in res
    assert "security reasons" in res.lower()

    # 3. Blocked DELETE
    res = await skill.run(query="DELETE FROM inventory WHERE id = 1")
    assert "Error" in res

    # 4. Blocked non-SELECT start
    res = await skill.run(query="-- some comment\nSELECT * FROM inventory")
    # Our regex allows leading whitespace/comments if SELECT follows
    assert isinstance(res, list)


@pytest.mark.asyncio
async def test_pandas_skill_analytics():
    r"""Verifies that PandasSkill correctly processes tabular data."""
    import importlib.util

    if importlib.util.find_spec("pandas") is None:
        pytest.skip("Pandas not installed")

    skill = PandasSkill()
    data = [{"val": 10}, {"val": 20}, {"val": 30}]

    # Sum
    res = await skill.run(data=data, operation="sum", column="val")
    assert res == 60.0

    # Missing column
    res = await skill.run(data=data, operation="mean", column="nonexistent")
    assert "Error" in res
