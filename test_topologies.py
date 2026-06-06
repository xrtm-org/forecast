#!/usr/bin/env python3
"""Test debate and consensus topologies with DeepSeek API. Cost-effective: 1 question each."""
import asyncio, os, sys
from pathlib import Path

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
from xrtm.data.corpora import load_real_binary_questions
from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.providers.inference.factory import ModelFactory
from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from xrtm.eval import BrierScoreEvaluator


async def test_direct(provider, question, resolved_outcome):
    """Direct ForecastingAnalyst baseline."""
    analyst = ForecastingAnalyst(model=provider, name="direct")
    forecast = await analyst.run(question)
    outcome = "yes" if resolved_outcome else "no"
    brier = BrierScoreEvaluator().score(forecast.probability, outcome)
    return forecast.probability, brier, forecast.reasoning[:150]


async def test_debate(provider, question, resolved_outcome):
    """Pro/Con/Judge debate topology. 3 LLM calls."""
    print("  [1/3] Pro agent...")
    pro_analyst = ForecastingAnalyst(model=provider, name="pro")
    pro_result = await pro_analyst.run(question)

    print("  [2/3] Con agent...")
    con_prompt = f"You are a skeptical forecaster. Challenge assumptions. Question: {question.title}"
    con_result = await provider.generate_content_async(
        f"Challenge this forecast analysis and provide a counter-probability. "
        f"Pro agent gave {pro_result.probability:.2f} with reasoning: {pro_result.reasoning[:300]}. "
        f"Give your counter-probability (0-1) and brief reasoning."
    )

    print("  [3/3] Judge agent...")
    con_text = con_result.text[:500]
    judge_prompt = (
        f"Question: {question.title}\n\n"
        f"Pro argument (p={pro_result.probability:.2f}): {pro_result.reasoning[:300]}\n\n"
        f"Con argument: {con_text}\n\n"
        f"Synthesize a final probability (0-1). Return JSON: {{\"probability\": float, \"reasoning\": text}}"
    )
    judge_result = await provider.generate_content_async(judge_prompt)

    # Parse judge
    import json
    try:
        judge_data = json.loads(judge_result.text)
        final_p = float(judge_data["probability"])
    except Exception:
        # Try to extract from text
        import re
        match = re.search(r'"probability":\s*([\d.]+)', judge_result.text)
        final_p = float(match.group(1)) if match else pro_result.probability

    outcome = "yes" if resolved_outcome else "no"
    brier = BrierScoreEvaluator().score(final_p, outcome)
    return final_p, brier, judge_result.text[:150] if hasattr(judge_result, 'text') else str(judge_result)[:150]


async def main():
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
    config = OpenAIConfig(
        model_id=os.environ.get("OPENAI_MODEL", "deepseek-v4-pro"),
        base_url=base_url.rstrip("/"),
        api_key=SecretStr(os.environ.get("OPENAI_API_KEY", "")),
        timeout=120,
    )
    provider = ModelFactory.get_provider(config)

    # Pick 2 interesting questions
    questions = list(load_real_binary_questions())
    q1 = questions[1]  # BoE rate hike (outcome: false) - tricky
    q2 = questions[6]  # S&P 500 (outcome: true) - benchmark got wrong

    for label, q in [("Q1-BoE", q1), ("Q2-SP500", q2)]:
        resolved = q.metadata.raw_data.get("resolved_outcome") if q.metadata else True
        outcome = "yes" if resolved else "no"
        print(f"\n{'='*60}")
        print(f"TOPOLOGY TEST: {label}")
        print(f"Question: {q.title}")
        print(f"Actual outcome: {outcome}")
        print(f"{'='*60}")

        # Direct
        print("\n--- Direct Analyst ---")
        dp, db, dr = await test_direct(provider, q, resolved)
        print(f"  Probability: {dp:.4f}  Brier: {db:.4f}")

        # Debate
        print("\n--- Debate Topology (Pro/Con/Judge) ---")
        dep, deb, der = await test_debate(provider, q, resolved)
        print(f"  Probability: {dep:.4f}  Brier: {deb:.4f}")

        print(f"\n  Comparison: Direct={dp:.3f} vs Debate={dep:.3f} (actual={outcome})")

    print(f"\n{'='*60}")
    print("TOPOLOGY TESTS COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
