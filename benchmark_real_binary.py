#!/usr/bin/env python3
"""Benchmark: run all 25 real-binary questions through DeepSeek, score against actual outcomes."""
import asyncio
import os
import sys
from pathlib import Path

# Load .env
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

from pydantic import SecretStr


async def main():
    from xrtm.data.corpora import load_real_binary_questions
    from xrtm.data.core.schemas.forecast import ForecastQuestion
    from xrtm.forecast.core.config.inference import OpenAIConfig
    from xrtm.forecast.providers.inference.factory import ModelFactory
    from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst
    from xrtm.eval import BrierScoreEvaluator, ExpectedCalibrationErrorEvaluator

    questions = list(load_real_binary_questions())
    print(f"Loaded {len(questions)} questions from real-binary corpus\n")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
    config = OpenAIConfig(
        model_id=os.environ.get("OPENAI_MODEL", "deepseek-v4-pro"),
        base_url=base_url.rstrip("/"),
        api_key=SecretStr(os.environ.get("OPENAI_API_KEY", "")),
        timeout=120,
    )
    provider = ModelFactory.get_provider(config)
    analyst = ForecastingAnalyst(model=provider, name="benchmark-analyst")
    brier = BrierScoreEvaluator()
    ece_eval = ExpectedCalibrationErrorEvaluator()

    predictions = []
    results = []

    for i, q in enumerate(questions):
        # Get resolved outcome (True/False -> yes/no)
        resolved = q.metadata.raw_data.get("resolved_outcome") if q.metadata else None
        if resolved is None:
            continue
        outcome = "yes" if resolved else "no"

        print(f"[{i+1}/{len(questions)}] {q.title[:80]}...")
        try:
            forecast = await analyst.run(q)
        except Exception as exc:
            print(f"  FAILED: {exc}")
            continue

        prob = forecast.probability
        brier_score = brier.score(prob, outcome)
        predictions.append((prob, outcome))
        results.append({
            "id": str(q.id)[:40],
            "title": q.title[:80],
            "probability": prob,
            "outcome": outcome,
            "brier": brier_score,
        })
        print(f"  p={prob:.3f}  outcome={outcome}  brier={brier_score:.4f}")

    if not predictions:
        print("No predictions generated.")
        return

    # Aggregate
    from xrtm.eval import summarize_binary_forecasts
    summary = summarize_binary_forecasts(predictions)

    print(f"\n{'='*60}")
    print(f"BENCHMARK SUMMARY — {len(predictions)} questions")
    print(f"{'='*60}")
    probs = [p[0] for p in predictions]
    outcomes_01 = [1.0 if p[1] == "yes" else 0.0 for p in predictions]
    mean_brier = sum((p - o) ** 2 for p, o in zip(probs, outcomes_01)) / len(predictions)
    accuracy = sum(1 for p, o in zip(probs, outcomes_01) if (p >= 0.5) == (o >= 0.5)) / len(predictions)

    print(f"Mean Brier:     {mean_brier:.4f}")
    print(f"ECE:            {summary.get('ece', 'N/A')}")
    print(f"Accuracy (>0.5): {accuracy:.2%}")
    print(f"Mean prob (yes): {sum(p for p, o in zip(probs, outcomes_01) if o >= 0.5) / max(1, sum(outcomes_01)):.3f}" if sum(outcomes_01) > 0 else "")
    print(f"Mean prob (no):  {sum(p for p, o in zip(probs, outcomes_01) if o < 0.5) / max(1, len(outcomes_01) - sum(outcomes_01)):.3f}" if sum(outcomes_01) < len(outcomes_01) else "")

    # Per-question table
    print(f"\n{'Question':<45} {'Prob':>6} {'Outcome':>8} {'Brier':>7}")
    print("-" * 68)
    for r in sorted(results, key=lambda r: r["brier"]):
        print(f"{r['id']:<45} {r['probability']:>6.3f} {r['outcome']:>8} {r['brier']:>7.4f}")

    print(f"\n{'='*60}")
    print("BENCHMARK COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
