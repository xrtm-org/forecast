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

import asyncio

import pytest

from xrtm.forecast.core.memory.graph import Fact
from xrtm.forecast.providers.memory.sqlite_kg import SQLiteFactStore


def _fact(subject: str, predicate: str = "status", value: str = "ok") -> Fact:
    return Fact(subject=subject, predicate=predicate, object_value=value)


@pytest.mark.asyncio
async def test_sqlite_fact_store_persists_and_filters(tmp_path):
    path = tmp_path / "facts.db"
    store = SQLiteFactStore(str(path))

    await store.remember(_fact("xrtm", "status", "ready"))
    await store.remember(_fact("xrtm", "owner", "local"))

    facts = await store.query("xrtm")
    status = await store.query("xrtm", "status")

    assert {fact.predicate for fact in facts} == {"status", "owner"}
    assert status[0].object_value == "ready"
    store.close()

    reopened = SQLiteFactStore(str(path))
    assert (await reopened.query("xrtm", "owner"))[0].object_value == "local"
    reopened.close()


@pytest.mark.asyncio
async def test_sqlite_fact_store_concurrent_operations(tmp_path):
    store = SQLiteFactStore(str(tmp_path / "facts.db"))

    await asyncio.gather(*(store.remember(_fact(f"subject-{i}", value=str(i))) for i in range(100)))
    results = await asyncio.gather(*(store.query(f"subject-{i}") for i in range(100)))

    assert all(len(result) == 1 for result in results)
    assert {result[0].subject for result in results} == {f"subject-{i}" for i in range(100)}
    store.close()


@pytest.mark.asyncio
async def test_sqlite_fact_store_forget_and_close(tmp_path):
    store = SQLiteFactStore(str(tmp_path / "facts.db"))

    await store.remember(_fact("xrtm"))
    await store.forget("xrtm", "status")
    assert await store.query("xrtm") == []

    store.close()
    with pytest.raises(RuntimeError, match="closed"):
        await store.query("xrtm")
