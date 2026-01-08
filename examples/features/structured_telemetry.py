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

from forecast.telemetry import SpanKind, telemetry_manager


async def simulate_work():
    r"""
    Simulates a sequence of reasoning steps with telemetry tracing.
    """
    # 1. Start a Trace
    telemetry_manager.start_trace()

    # 2. Start a Root Span
    with telemetry_manager.start_span("forecast_execution", attributes={"subject": "BTC_Price"}):
        print("Executing Root Span...")
        await asyncio.sleep(0.1)

        # 3. Start a Child Span (Reasoning)
        with telemetry_manager.start_span("reasoning_node", kind=SpanKind.INTERNAL):
            print("  Executing Reasoning Node...")
            telemetry_manager.add_event("thinking_started")
            await asyncio.sleep(0.2)
            telemetry_manager.add_event("thinking_finished", attributes={"confidence": 0.85})

        # 4. Start another Child Span (Search)
        with telemetry_manager.start_span("search_skill", kind=SpanKind.CLIENT):
            print("  Executing Search Skill...")
            await asyncio.sleep(0.1)

    # 6. Export
    path = telemetry_manager.export_trace()
    print(f"\nTrace exported to: {path}")


async def main():
    # Note: TelemetryManager doesn't support 'with' yet, I should add that for better DX.
    # For now, manually ending.
    await simulate_work()


if __name__ == "__main__":
    asyncio.run(main())
