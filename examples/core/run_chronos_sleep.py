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
import time
from datetime import datetime

from forecast import AsyncRuntime, BaseGraphState, Orchestrator, TemporalContext


async def sleep_stage(state, on_progress=None):
    r"""A stage that performs multiple long sleeps."""
    print(f"[STAGE] Execution started at {datetime.now().time()}")

    # We sleep for 60 seconds total
    await AsyncRuntime.sleep(30.0)
    print("[STAGE] 30s virtual seconds passed...")
    await AsyncRuntime.sleep(30.0)
    print("[STAGE] Another 30s virtual seconds passed...")

    return None


async def run_chronos_demo():
    r"""Demonstrates Chronos-Sleep acceleration during backtests."""
    print("--- [CHRONOS-SLEEP ACCELERATION DEMO] ---")

    # 1. LIVE MODE (Standard Sleep)
    print("\n[LIVE MODE] Starting reasoning cycle (no temporal context)...")
    state_live = BaseGraphState(subject_id="live-test")
    orch = Orchestrator()
    orch.add_node("sleepy", sleep_stage)
    orch.set_entry_point("sleepy")

    # We'll cancel this after a second because we don't want to wait 60s in a demo
    try:
        start_live = time.time()
        print("Note: Live mode would actually wait 60 seconds. We'll timeout for this demo.")
        await asyncio.wait_for(orch.run(state_live), timeout=0.5)
    except asyncio.TimeoutError:
        print(f"Live mode timed out as expected after {time.time() - start_live:.2f}s")

    # 2. BACKTEST MODE (Instant Sleep)
    print("\n[BACKTEST MODE] Starting reasoning cycle (with TemporalContext)...")
    state_bt = BaseGraphState(
        subject_id="bt-test", temporal_context=TemporalContext(reference_time=datetime(2023, 1, 1), is_backtest=True)
    )

    start_bt = time.time()
    await orch.run(state_bt)
    end_bt = time.time()

    print(f"\nBacktest completed in {end_bt - start_bt:.4f}s")
    print("Chronos-Sleep successfully bypassed 60 seconds of real-world delay.")


if __name__ == "__main__":
    asyncio.run(run_chronos_demo())
