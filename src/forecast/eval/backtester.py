import logging
from typing import List, Tuple

from forecast.agents.base import Agent
from forecast.eval.definitions import EvaluationReport, EvaluationResult, Evaluator
from forecast.schemas.forecast import ForecastQuestion, ForecastResolution

logger = logging.getLogger(__name__)

class Backtester:
    """
    Orchestrates the evaluation of an Agent against a dataset of Questions and Resolutions.
    """
    def __init__(self, agent: Agent, evaluator: Evaluator):
        self.agent = agent
        self.evaluator = evaluator

    async def run(self, dataset: List[Tuple[ForecastQuestion, ForecastResolution]]) -> EvaluationReport:
        """
        Runs the agent against the dataset and evaluates results.
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
                    prediction=conf,
                    ground_truth=resolution.outcome,
                    subject_id=question.id
                )

                results.append(eval_res)
                total_score += eval_res.score

            except Exception as e:
                logger.error(f"Failed to evaluate question {question.id}: {e}")

        count = len(results)
        mean_score = total_score / count if count > 0 else 0.0

        return EvaluationReport(
            metric_name="Brier Score",
            mean_score=mean_score,
            total_evaluations=count,
            results=results
        )
