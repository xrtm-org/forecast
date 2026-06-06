#!/usr/bin/env python3
"""End-to-end forecast test: data -> forecast -> eval with DeepSeek API."""
import asyncio
import os
from pathlib import Path

from pydantic import SecretStr


async def main():
    # Load .env from workspace root
    env_path = Path("/home/moy/workspaces/xrtm/.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    line = line[7:]
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    # --- Layer 1: Data ---
    from xrtm.data.corpora import load_real_binary_questions
    questions = load_real_binary_questions(limit=1)
    question = questions[0]
    print(f"Question ID:  {question.id}")
    print(f"Title:        {question.title}")
    print(f"Description:  {question.description}")
    print()

    # --- Layer 3: Forecast ---
    from xrtm.forecast.core.config.inference import OpenAIConfig
    from xrtm.forecast.providers.inference.factory import ModelFactory
    from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
    config = OpenAIConfig(
        model_id=os.environ.get("OPENAI_MODEL", "deepseek-v4-pro"),
        base_url=base_url.rstrip("/"),
        api_key=SecretStr(os.environ.get("OPENAI_API_KEY", "")),
        timeout=120,
    )
    provider = ModelFactory.get_provider(config)
    analyst = ForecastingAnalyst(model=provider, name="e2e-analyst")

    print("Generating forecast via DeepSeek...")
    forecast = await analyst.run(question)

    print(f"\n{'='*60}")
    print("FORECAST RESULT")
    print(f"{'='*60}")
    print(f"Probability: {forecast.probability:.4f}")
    print(f"Confidence:  {getattr(forecast, 'confidence_interval', 'N/A')}")
    print(f"Reasoning:   {forecast.reasoning[:500]}...")
    print(f"Trace nodes: {len(forecast.logical_trace)}")
    print()

    # --- Layer 2: Eval ---
    from xrtm.eval import BrierScoreEvaluator, summarize_binary_forecasts

    mock_outcome = "yes"
    prediction = (forecast.probability, mock_outcome)
    summary = summarize_binary_forecasts([prediction])
    print(f"{'='*60}")
    print(f"SCORING (mock resolution='{mock_outcome}')")
    print(f"{'='*60}")
    print(f"Brier score:    {summary['brier_score']:.4f}")
    print(f"ECE:            {summary['ece']:.4f}")
    print(f"Log score:      {summary['log_score']:.4f}")
    print(f"# resolved:     {summary['resolved_count']}")
    print(f"Reliability:   {summary['reliability']:.4f}")
    print(f"Resolution:    {summary['resolution']:.4f}")
    print(f"Uncertainty:   {summary['uncertainty']:.4f}")

    print(f"\n{'='*60}")
    print("END-TO-END PIPELINE: data -> forecast -> eval  OK")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
