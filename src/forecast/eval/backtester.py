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

import logging
from typing import List, Tuple

from forecast.agents.base import Agent
from forecast.eval.definitions import EvaluationReport, EvaluationResult, Evaluator
from forecast.schemas.forecast import ForecastQuestion, ForecastResolution

logger = logging.getLogger(__name__)


class Backtester:
    r"""
    An orchestrator for evaluating Agent performance against historical data.

    `Backtester` takes an agent and an evaluator, runs the agent against a series
    of questions, and produces an aggregate performance report using the evaluator's
    logic.

    Args:
        agent (`Agent`):
            The agent instance to be tested.
        evaluator (`Evaluator`):
            The metric implementation to use for scoring.
    """

    def __init__(self, agent: Agent, evaluator: Evaluator):
        self.agent = agent
        self.evaluator = evaluator

    async def run(self, dataset: List[Tuple[ForecastQuestion, ForecastResolution]]) -> EvaluationReport:
        r"""
        Executes the backtesting suite against a provided dataset.

        Args:
            dataset (`List[Tuple[ForecastQuestion, ForecastResolution]]`):
                A list of (question, resolution) pairs to evaluate.

        Returns:
            `EvaluationReport`: A high-level summary of the agent's performance.
        """
        results: List[EvaluationResult] = []
        total_score = 0.0

        for question, resolution in dataset:
            try:
                logger.info(f"Backtesting question: {question.id}")
                # Run the agent
                prediction = await self.agent.run(question)

                # Extract confidence from Prediction (handling ForecastOutput objects)
                conf = getattr(prediction, "confidence", prediction)

                # Evaluate
                eval_res = self.evaluator.evaluate(
                    prediction=conf, ground_truth=resolution.outcome, subject_id=question.id
                )

                results.append(eval_res)
                total_score += eval_res.score

            except Exception as e:
                logger.error(f"Failed to evaluate question {question.id}: {e}")

        count = len(results)
        mean_score = total_score / count if count > 0 else 0.0

        return EvaluationReport(
            metric_name="Brier Score", mean_score=mean_score, total_evaluations=count, results=results
        )


__all__ = ["Backtester"]
