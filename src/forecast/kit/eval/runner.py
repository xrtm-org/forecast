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
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from forecast.core.eval.definitions import EvaluationReport, EvaluationResult, Evaluator
from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.forecast import ForecastOutput, ForecastQuestion, ForecastResolution
from forecast.core.schemas.graph import BaseGraphState, TemporalContext
from forecast.kit.eval.analytics import SliceAnalytics
from forecast.kit.eval.metrics import BrierScoreEvaluator, ExpectedCalibrationErrorEvaluator

logger = logging.getLogger(__name__)


class BacktestInstance(BaseModel):
    r"""
    A single data point for a historical backtest.

    Attributes:
        question (`ForecastQuestion`):
            The question/task to be performed.
        resolution (`ForecastResolution`):
        reference_time (`datetime`):
            The point in time to which the system should be "rewound".
    """

    question: ForecastQuestion
    resolution: ForecastResolution
    reference_time: datetime
    tags: Optional[List[str]] = None


class BacktestDataset(BaseModel):
    r"""A collection of historical instances for batch evaluation."""

    name: str = "default_backtest"
    items: List[BacktestInstance]


class BacktestRunner:
    r"""
    An industrial-grade engine for executing large-scale historical backtests.

    The `BacktestRunner` manages the temporal lifecycle of multiple graph executions,
    ensuring that each run is isolated within its own `TemporalContext`. It supports
    asynchronous parallel execution and produces aggregate calibration reports.

    Args:
        orchestrator (`Orchestrator`):
            The pre-wired graph orchestrator to execute.
        evaluator (`Evaluator`, *optional*):
            The metric engine for scoring results. Defaults to `BrierScoreEvaluator`.
        entry_node (`str`, *optional*, defaults to `"ingestion"`):
            The starting node in the graph.
        concurrency (`int`, *optional*, defaults to `5`):
            Maximum number of concurrent backtest simulations.
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        evaluator: Optional[Evaluator] = None,
        entry_node: str = "ingestion",
        concurrency: int = 5,
    ):
        self.orchestrator = orchestrator
        self.evaluator = evaluator or BrierScoreEvaluator()
        self.entry_node = entry_node
        self.semaphore = asyncio.Semaphore(concurrency)

    async def _run_single(self, instance: BacktestInstance) -> EvaluationResult:
        r"""Executes a single backtest instance within a semaphore-controlled block."""
        async with self.semaphore:
            # 1. Prepare the state with Temporal Context
            state = BaseGraphState(
                subject_id=instance.question.id,
                temporal_context=TemporalContext(reference_time=instance.reference_time, is_backtest=True),
            )
            # Inject question info into metadata/context if needed
            # For now, we assume nodes know how to extract query from somewhere or we put it in node_reports
            state.node_reports["ingestion"] = instance.question.title
            if instance.question.content:
                state.node_reports["ingestion"] += f"\n\nContext: {instance.question.content}"

            try:
                # 2. Run the graph
                await self.orchestrator.run(state, entry_node=self.entry_node)

                # 3. Extract and Evaluate
                return self.evaluate_state(
                    state, instance.resolution, instance.question.id, instance.reference_time, instance.tags
                )

            except Exception as e:
                logger.error(f"Backtest error on {instance.question.id}: {e}")
                return EvaluationResult(
                    subject_id=instance.question.id,
                    score=1.0,  # Worst possible Brier score on error
                    ground_truth=instance.resolution.outcome,
                    prediction=0.5,
                    metadata={"error": str(e)},
                )

    def evaluate_state(
        self,
        state: BaseGraphState,
        resolution: ForecastResolution,
        subject_id: str,
        reference_time: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
    ) -> EvaluationResult:
        r"""
        Evaluates a completed graph state against a known resolution.

        This method is exposed publically to allow 'Trace Replay' offline evaluation.

        Args:
            state: The final state of the graph execution.
            resolution: The ground truth resolution object.
            subject_id: The identifier of the question.
            reference_time: Optional timestamp for metadata.
            tags: Optional tags for metadata.

        Returns:
            EvaluationResult: The scoring outcome.
        """
        # 1. Extract prediction (defaulting to 0.5)
        prediction_val = 0.5

        # Check for ForecastOutput in node_reports
        # We prioritize specific types, then dicts, then raw values
        for report in reversed(list(state.node_reports.values())):
            if isinstance(report, ForecastOutput):
                prediction_val = report.confidence
                break
            elif isinstance(report, dict) and "confidence" in report:
                prediction_val = float(report["confidence"])
                break
            elif isinstance(report, (int, float)):
                prediction_val = float(report)
                break

        # 2. Parse Ground Truth
        outcome_raw = resolution.outcome
        if isinstance(outcome_raw, str):
            if outcome_raw.lower() in ["true", "yes", "1", "pass"]:
                gt_val = 1.0
            elif outcome_raw.lower() in ["false", "no", "0", "fail"]:
                gt_val = 0.0
            else:
                try:
                    gt_val = float(outcome_raw)
                except ValueError:
                    logger.warning(f"Could not parse ground truth '{outcome_raw}' as float. Defaulting to 0.0.")
                    gt_val = 0.0
        else:
            gt_val = float(outcome_raw)

        # 3. Compute Score
        eval_res = self.evaluator.evaluate(prediction=prediction_val, ground_truth=gt_val, subject_id=subject_id)

        # 4. Add Metadata
        if reference_time:
            eval_res.metadata["reference_time"] = reference_time.isoformat()

        eval_res.metadata["total_latency"] = sum(state.latencies.values())
        if tags:
            eval_res.metadata["tags"] = tags

        return eval_res

    async def run(self, dataset: BacktestDataset) -> EvaluationReport:
        r"""
        Executes the backtest across the entire dataset in parallel.

        Args:
            dataset (`BacktestDataset`):
                The collection of historical instances to test.

        Returns:
            `EvaluationReport`: The aggregated performance metrics.
        """
        logger.info(f"Starting backtest '{dataset.name}' with {len(dataset.items)} instances.")

        tasks = [self._run_single(item) for item in dataset.items]
        results = await asyncio.gather(*tasks)

        total_score = sum(r.score for r in results)
        count = len(results)
        mean_score = total_score / count if count > 0 else 0.0

        # Calculate ECE and reliability data
        ece_evaluator = ExpectedCalibrationErrorEvaluator()
        ece_score, ece_bins = ece_evaluator.compute_calibration_data(results)

        # Compute Slices
        slices = SliceAnalytics.compute_slices(results)

        return EvaluationReport(
            metric_name=getattr(self.evaluator, "name", "Brier Score"),
            mean_score=mean_score,
            total_evaluations=count,
            results=results,
            reliability_bins=ece_bins,
            summary_statistics={"ece": ece_score},
            slices=slices,
        )


__all__ = ["BacktestInstance", "BacktestDataset", "BacktestRunner"]
