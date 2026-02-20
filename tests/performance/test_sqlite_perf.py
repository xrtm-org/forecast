import asyncio
import os
import statistics
import time
from datetime import datetime, timezone

from xrtm.forecast.core.memory.graph import Fact
from xrtm.forecast.providers.memory.sqlite_kg import SQLiteFactStore

DB_PATH = "perf_test.db"

async def heartbeat(monitor_data, stop_event):
    while not stop_event.is_set():
        expected_sleep = 0.01
        start = time.perf_counter()
        await asyncio.sleep(expected_sleep)
        end = time.perf_counter()
        actual_sleep = end - start
        delay = actual_sleep - expected_sleep
        monitor_data.append(delay)

async def run_benchmark():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    store = SQLiteFactStore(db_path=DB_PATH)

    num_facts = 100
    facts = [
        Fact(
            subject=f"sub_{i}",
            predicate="is_a",
            object_value=f"obj_{i}",
            verified_at=datetime.now(timezone.utc),
            confidence=1.0
        )
        for i in range(num_facts)
    ]

    monitor_data = []
    stop_event = asyncio.Event()

    # Start heartbeat
    heartbeat_task = asyncio.create_task(heartbeat(monitor_data, stop_event))

    start_time = time.perf_counter()

    # Insert facts
    for fact in facts:
        await store.remember(fact)
        # Force yield to allow heartbeat to run
        await asyncio.sleep(0)

    end_time = time.perf_counter()

    stop_event.set()
    await heartbeat_task

    total_time = end_time - start_time
    avg_latency = total_time / len(facts)

    print(f"Total time: {total_time:.4f}s")
    print(f"Average insertion time: {avg_latency*1000:.4f}ms")

    if monitor_data:
        max_delay = max(monitor_data)
        avg_delay = statistics.mean(monitor_data)
        print(f"Max event loop delay: {max_delay*1000:.4f}ms")
        print(f"Avg event loop delay: {avg_delay*1000:.4f}ms")
        print(f"Number of heartbeat samples: {len(monitor_data)}")
    else:
        print("No heartbeat data collected")

    # Verify data
    print("Verifying data...")
    retrieved_facts = []
    for i in range(num_facts):
        subject = f"sub_{i}"
        results = await store.query(subject)
        retrieved_facts.extend(results)

    print(f"Retrieved {len(retrieved_facts)} facts.")
    if len(retrieved_facts) == num_facts:
        print("Data verification successful.")
    else:
        print(f"Data verification FAILED. Expected {num_facts}, got {len(retrieved_facts)}.")

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
