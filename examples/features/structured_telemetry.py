import asyncio

from forecast.telemetry import SpanKind, telemetry_manager


async def simulate_work():
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
