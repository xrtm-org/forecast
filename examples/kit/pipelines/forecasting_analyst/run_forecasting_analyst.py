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
import logging
import os

from pydantic import SecretStr
from xrtm.data.providers.data.local import LocalDataSource

from xrtm.forecast.core.config.inference import GeminiConfig
from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from xrtm.forecast.kit.pipelines.analyst import GenericAnalystPipeline
from xrtm.forecast.providers.inference.factory import ModelFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("showcase")


async def run_showcase():
    r"""
    Executes the standard forecasting analyst showcase pipeline.
    """
    # 1. Setup Inference
    # Ensure GEMINI_API_KEY is set in your environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found. Please set it in your .env file.")
        return

    config = GeminiConfig(
        model_id="gemini-2.0-flash-lite",
        api_key=SecretStr(api_key),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    )
    provider = ModelFactory.get_provider(config)

    # 2. Setup Data Source (Local mode for stability)
    data_source = LocalDataSource("examples/kit/pipelines/forecasting_analyst/data/subject_sample.json")

    # 3. Setup Agent & Pipeline
    analyst = ForecastingAnalyst(model=provider)
    pipeline = GenericAnalystPipeline(data_source=data_source, analyst=analyst)

    # 4. Run for a specific subject
    target_subject_id = "fed-rates-mar-2026"

    async def on_progress(p_id, phase, status, details, specialists=None):
        print(f"[{phase}] {status}: {details}")

    print(f"\n>>> Starting Forecast for: {target_subject_id}")
    state = await pipeline.run(subject_id=target_subject_id, on_progress=on_progress)

    # 5. Output Results
    print("\n" + "=" * 50)
    print(state.context.get("report", "No report generated."))
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(run_showcase())
