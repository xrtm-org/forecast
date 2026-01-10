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
from typing import Optional

from forecast.core.eval.definitions import EvaluationResult, Evaluator
from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.forecast import ForecastResolution
from forecast.core.schemas.graph import BaseGraphState
from forecast.kit.eval.runner import BacktestRunner

__all__ = ["TraceReplayer"]


logger = logging.getLogger(__name__)


class TraceReplayer:
    r"""
    A utility for deterministic replay of graph execution traces.

    This class enables "Offline Evaluation" by loading serialized graph states
    and re-running the evaluation logic without incurring the cost of re-generating
    the LLM outputs.
    """

    @staticmethod
    def save_trace(state: BaseGraphState, path: str) -> None:
        r"""
        Serializes the graph state to a JSON file.

        Args:
            state: The completed graph state.
            path: The file path to save the trace to.
        """
        try:
            json_str = state.model_dump_json(indent=2)
            with open(path, "w", encoding="utf-8") as f:
                f.write(json_str)
            logger.info(f"Trace saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save trace to {path}: {e}")
            raise

    @staticmethod
    def load_trace(path: str) -> BaseGraphState:
        r"""
        Deserializes a graph state from a JSON file.

        Args:
            path: The file path to load the trace from.

        Returns:
            BaseGraphState: The reconstructed state object.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                json_str = f.read()
            state = BaseGraphState.model_validate_json(json_str)
            return state
        except Exception as e:
            logger.error(f"Failed to load trace from {path}: {e}")
            raise

    def replay_evaluation(
        self,
        trace_path: str,
        resolution: ForecastResolution | float | str,
        evaluator: Optional[Evaluator] = None,
        subject_id_override: Optional[str] = None,
    ) -> EvaluationResult:
        r"""
        Loads a trace and re-runs the evaluation logic offline.

        Args:
            trace_path (`str`):
                Path to the saved trace JSON file.
            resolution (`ForecastResolution` | `float` | `str`):
                The ground truth outcome to grade against. Can be a full object,
                a raw float (0-1), or a string ("True"/"False").
            evaluator (`Evaluator`, *optional*):
                The evaluator engine to use. Defaults to `BrierScoreEvaluator`
                via the internal `BacktestRunner`.
            subject_id_override (`str`, *optional*):
                Optional ID to use if different from the ID stored in the trace.

        Returns:
            `EvaluationResult`:
                The scoring outcome from the offline replay, including metadata
                marking it as a replay.
        """
        # 1. Load Trace
        state = self.load_trace(trace_path)

        subject_id = subject_id_override or state.subject_id

        # 2. Normalize Resolution
        if not isinstance(resolution, ForecastResolution):
            resolution = ForecastResolution(
                question_id=subject_id, outcome=str(resolution), metadata={"source": "replay_override"}
            )

        # 3. Use Runner Logic
        # We create a dummy runner just to access the shared grading logic
        dummy_orch: Orchestrator[BaseGraphState] = Orchestrator()
        runner = BacktestRunner(orchestrator=dummy_orch, evaluator=evaluator)

        # 4. Execute Evaluation
        result = runner.evaluate_state(
            state=state,
            resolution=resolution,
            subject_id=subject_id,
            reference_time=state.temporal_context.reference_time if state.temporal_context else None,
        )

        result.metadata["is_replay"] = True
        return result
