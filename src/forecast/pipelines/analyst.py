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
from typing import Callable, Optional

from forecast.agents.specialists.analyst import ForecastingAnalyst
from forecast.data_sources.base import DataSource
from forecast.graph.config import GraphConfig
from forecast.graph.orchestrator import Orchestrator
from forecast.schemas.graph import BaseGraphState
from forecast.telemetry.audit import auditor

logger = logging.getLogger(__name__)


class GenericAnalystPipeline:
    """
    Standardized pipeline for fetching a question and generating an analyst forecast.
    """

    def __init__(
        self,
        data_source: DataSource,
        analyst: ForecastingAnalyst,
        config: Optional[GraphConfig] = None,
    ):
        self.data_source = data_source
        self.analyst = analyst
        self.config = config or GraphConfig()
        self.orchestrator = Orchestrator(config=self.config)
        self._setup_graph()

    def _setup_graph(self):
        self.orchestrator.register_node("ingestion", self._ingest_node)
        self.orchestrator.register_node("analysis", self._analyze_node)

    async def _ingest_node(self, state: BaseGraphState, on_progress: Callable) -> Optional[str]:
        await on_progress(1, "Ingestion", "PROCESSING", f"Fetching subject with ID: {state.subject_id}")
        question = await self.data_source.get_question_by_id(state.subject_id)
        if not question:
            await on_progress(1, "Ingestion", "ERROR", "Subject not found")
            return None

        state.context["question"] = question
        return "analysis"

    async def _analyze_node(self, state: BaseGraphState, on_progress: Callable) -> None:
        question = state.context["question"]
        await on_progress(2, "Analysis", "PROCESSING", f"Analyzing: {question.title}")

        output = await self.analyst.run(question)
        state.context["output"] = output

        await on_progress(2, "Analysis", "COMPLETE", f"Forecast generated: {output.confidence * 100:.1f}%")
        return None

    async def run(self, subject_id: str, on_progress: Optional[Callable] = None) -> BaseGraphState:
        """Runs the pipeline for a specific subject (e.g. question slug/ID)."""
        state = BaseGraphState(subject_id=subject_id)
        final_state = await self.orchestrator.run(state, entry_node="ingestion", on_progress=on_progress)

        # Post-run: Generate human-readable 'Double-Trace' report
        if "output" in final_state.context:
            report = auditor.generate_execution_report(final_state, final_state.context["output"])
            final_state.context["report"] = report

        return final_state
