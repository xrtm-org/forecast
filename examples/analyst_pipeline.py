import asyncio
import logging
import os

from pydantic import SecretStr

from forecast.agents.specialists.analyst import ForecastingAnalyst
from forecast.data_sources.local import LocalDataSource
from forecast.inference.config import GeminiConfig
from forecast.inference.factory import ModelFactory
from forecast.pipelines.analyst import GenericAnalystPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("showcase")

async def run_showcase():
    # 1. Setup Inference
    # Ensure GEMINI_API_KEY is set in your environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found. Please set it in your .env file.")
        return

    config = GeminiConfig(
        model_id="gemini-2.0-flash-lite",
        api_key=SecretStr(api_key),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0")
    )
    provider = ModelFactory.get_provider(config)

    # 2. Setup Data Source (Local mode for stability)
    data_source = LocalDataSource("examples/data/polymarket_sample.json")

    # 3. Setup Agent & Pipeline
    analyst = ForecastingAnalyst(model=provider)
    pipeline = GenericAnalystPipeline(data_source=data_source, analyst=analyst)

    # 4. Run for a specific market
    target_market_id = "fed-rates-mar-2026"

    async def on_progress(p_id, phase, status, details, specialists=None):
        print(f"[{phase}] {status}: {details}")

    print(f"\n>>> Starting Forecast for: {target_market_id}")
    state = await pipeline.run(subject_id=target_market_id, on_progress=on_progress)

    # 5. Output Results
    print("\n" + "="*50)
    print(state.context.get("report", "No report generated."))
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_showcase())
