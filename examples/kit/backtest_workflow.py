import asyncio
import os
from datetime import datetime

from forecast.core.config.inference import OpenAIConfig
from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.graph import BaseGraphState, TemporalContext
from forecast.kit.stages.guardian import LeakageGuardian
from forecast.providers.inference.openai_provider import OpenAIProvider
from forecast.providers.tools.search import TavilySearchTool


async def forecasting_node(state, report):
    # This node simulates a forecaster using tools
    # It will automatically have datetime.now() mocked to 2024-06-15
    print(f"\n[NODE] Reasoning at mocked time: {datetime.now()}")

    # Simulate tool call (In a real scenario, this would be via an Agent)
    TavilySearchTool()
    # The tool.run will automatically pick up temporal_context if passed
    # query = await tool.run(query="Nvidia stock news", temporal_context=state.temporal_context)

    state.node_reports["forecaster"] = "I predict the 2024 UK election results will be..."
    return "guardian"


async def main():
    # 1. Setup Inference for Guardian
    config = OpenAIConfig(model_id="gpt-4o", api_key=os.getenv("OPENAI_API_KEY", "fake"))
    provider = OpenAIProvider(config)
    guardian = LeakageGuardian(provider=provider)

    # 2. Setup Orchestrator
    orch = Orchestrator.create_standard()
    orch.add_node("forecaster", forecasting_node)
    orch.add_node("guardian", guardian)
    orch.set_entry_point("forecaster")

    # 3. Setup Backtest Context (Summer 2024)
    historical_time = datetime(2024, 6, 15)
    state = BaseGraphState(
        subject_id="demo_backtest", temporal_context=TemporalContext(reference_time=historical_time, is_backtest=True)
    )

    print("--- Running v0.2.0 Backtest Demo ---")
    print(f"Reference Time: {historical_time}")

    await orch.run(state)

    print(f"\nFinal Execution Path: {state.execution_path}")
    print("Final Node Reports Summary:")
    for node, report in state.node_reports.items():
        print(f"  - {node}: {str(report)[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
