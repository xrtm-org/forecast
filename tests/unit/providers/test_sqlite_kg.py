
import os
import tempfile
from datetime import datetime, timezone

import pytest

from xrtm.forecast.core.memory.graph import Fact
from xrtm.forecast.providers.memory.sqlite_kg import SQLiteFactStore


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        path = tmp.name
    # Close the file handle so SQLite can open it properly on Windows (though not strictly needed on Linux)
    tmp.close()
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

@pytest.mark.asyncio
async def test_sqlite_kg_lifecycle(db_path):
    store = SQLiteFactStore(db_path=db_path)

    # Test connection is open
    assert store.conn is not None

    fact = Fact(
        subject="test_subject",
        predicate="test_predicate",
        object_value="test_value",
        verified_at=datetime.now(timezone.utc)
    )

    # Test remember
    await store.remember(fact)

    # Test query
    facts = await store.query("test_subject")
    assert len(facts) == 1
    assert facts[0].object_value == "test_value"

    # Test forget
    await store.forget("test_subject")
    facts = await store.query("test_subject")
    assert len(facts) == 0

    # Test close
    store.close()

    # Verify connection is closed and reference is None
    assert store.conn is None

@pytest.mark.asyncio
async def test_sqlite_kg_persistence(db_path):
    # Create store and add data
    store1 = SQLiteFactStore(db_path=db_path)
    fact = Fact(
        subject="persistent_subject",
        predicate="p",
        object_value="v",
        verified_at=datetime.now(timezone.utc)
    )
    await store1.remember(fact)
    store1.close()

    # Open new store on same file
    store2 = SQLiteFactStore(db_path=db_path)
    facts = await store2.query("persistent_subject")
    assert len(facts) == 1
    assert facts[0].object_value == "v"
    store2.close()
