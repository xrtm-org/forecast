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

from forecast.core.config.inference import OpenAIConfig
from forecast.core.schemas.forecast import ForecastQuestion, ForecastResolution
from forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from forecast.kit.eval import Backtester, BrierScoreEvaluator
from forecast.providers.inference.factory import ModelFactory


async def main():
    # 1. Setup
    config = OpenAIConfig(api_key="mock-key", model_id="gpt-4o")
    factory = ModelFactory()
    model = factory.get_provider(config)

    # We'll use the specialist ForecastingAnalyst
    agent = ForecastingAnalyst(model=model)

    # 2. Prepare a Small Mock Dataset
    # Question 1: Will BTC hit $100k? (Predicted 0.8, Outcome 1)
    q1 = ForecastQuestion(id="q1", title="Will Bitcoin reach $100,000 by end of year?")
    r1 = ForecastResolution(question_id="q1", outcome="1")

    # Question 2: Will it rain in London? (Predicted 0.3, Outcome 0)
    q2 = ForecastQuestion(id="q2", title="Will it rain in London tomorrow?")
    r2 = ForecastResolution(question_id="q2", outcome="0")

    dataset = [(q1, r1), (q2, r2)]

    # 3. Setup Evaluator and Backtester
    evaluator = BrierScoreEvaluator()
    backtester = Backtester(agent=agent, evaluator=evaluator)

    print("--- Starting Backtest ---")
    # Note: This will call the 'model' which is mocked here, so results will depend on mock behavior.
    # For demonstration, we'll just show the plumbing.

    # To avoid actual API calls in this demo, let's mock the agent.run
    async def mock_run(question):
        # Return hardcoded confidences for the demo
        if question.id == "q1":
            return 0.8
        return 0.3

    agent.run = mock_run

    report = await backtester.run(dataset)

    print(f"\nReport Metric: {report.metric_name}")
    print(f"Total Evaluations: {report.total_evaluations}")
    print(f"Mean Score (Brier): {report.mean_score:.4f}")

    for res in report.results:
        print(f"  - Subject {res.subject_id}: Pred={res.prediction}, Truth={res.ground_truth}, Score={res.score:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
