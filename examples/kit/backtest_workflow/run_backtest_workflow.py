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
from datetime import datetime

from forecast.core.config.inference import OpenAIConfig
from forecast.core.orchestrator import Orchestrator
from forecast.core.runtime import AsyncRuntime
from forecast.core.schemas.graph import BaseGraphState, TemporalContext
from forecast.core.stages.guardian import LeakageGuardian
from forecast.providers.inference.openai_provider import OpenAIProvider
from forecast.providers.tools.search import TavilySearchTool


async def forecasting_stage(state, report):
    r"""A demo stage representing a forecaster utilizing the temporal sandbox."""
    # This stage simulates a forecaster using tools
    # It will automatically have datetime.now() mocked to 2024-06-15
    print(f"\n[STAGE] Reasoning at mocked time: {datetime.now()}")

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
    orch.add_node("forecaster", forecasting_stage)
    orch.add_node("guardian", guardian)
    orch.set_entry_point("forecaster")

    # 3. Setup Backtest Context (Summer 2024)
    historical_time = datetime(2024, 6, 15)
    state = BaseGraphState(
        subject_id="demo_backtest", temporal_context=TemporalContext(reference_time=historical_time, is_backtest=True)
    )

    from forecast import __version__

    print(f"--- Running v{__version__} Backtest Demo ---")
    print(f"Reference Time: {historical_time}")

    await orch.run(state)

    print(f"\nFinal Execution Path: {state.execution_path}")
    print("Final Node Reports Summary:")
    for node, report in state.node_reports.items():
        print(f"  - {node}: {str(report)[:100]}...")


if __name__ == "__main__":
    AsyncRuntime.run_main(main())
