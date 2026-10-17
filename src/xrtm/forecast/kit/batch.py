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

r"""Batch forecasting with bounded concurrency and budget enforcement.

Example:
    >>> from xrtm.forecast.kit.batch import forecast_many
    >>> result = await forecast_many(agent, questions, concurrency=5)  # doctest: +SKIP
    >>> len(result.outputs)  # doctest: +SKIP
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Iterable, List, Optional

from pydantic import BaseModel, Field
from xrtm.data.core.schemas.forecast import ForecastOutput, ForecastQuestion

from xrtm.forecast.core.policies.cost import BudgetPolicy, CostLedger

logger = logging.getLogger(__name__)

__all__ = ["BatchForecastResult", "forecast_many"]


class BatchForecastResult(BaseModel):
    r"""Aggregated result of a batch forecast run.

    Attributes:
        outputs: Successfully produced forecasts.
        errors: ``"<question id>: <error>"`` strings for failed forecasts.
        skipped: Number of forecasts skipped because the budget was exhausted.
        cost: Cost incurred by this batch (in ``currency``).
        currency: Currency of ``cost`` (empty when no ledger was provided).
    """

    outputs: List[ForecastOutput] = Field(default_factory=list, description="Successfully produced forecasts")
    errors: List[str] = Field(default_factory=list, description="Failures as '<question id>: <error>'")
    skipped: int = Field(default=0, description="Forecasts skipped because the budget was exhausted")
    cost: float = Field(default=0.0, description="Cost incurred by this batch")
    currency: str = Field(default="", description="Currency of the batch cost")


def _agent_model_id(agent: Any) -> str:
    model = getattr(agent, "model", None)
    return str(getattr(model, "model_id", "") or "")


async def forecast_many(
    agent: Any,
    questions: Iterable[ForecastQuestion],
    concurrency: int = 5,
    ledger: Optional[CostLedger] = None,
    budget: Optional[BudgetPolicy] = None,
    model_id: Optional[str] = None,
) -> BatchForecastResult:
    r"""Forecast many questions concurrently, respecting a budget when provided.

    Args:
        agent: Any object with ``async run(question) -> ForecastOutput``.
        questions: Questions to forecast.
        concurrency: Maximum in-flight forecasts.
        ledger: Optional :class:`CostLedger`; when provided, each output's usage is priced.
        budget: Optional :class:`BudgetPolicy`; remaining questions are skipped once exceeded.
        model_id: Model id used for pricing (defaults to the agent's provider model id).

    Returns:
        BatchForecastResult: outputs, errors, skips, and batch cost.
    """
    questions = list(questions)
    semaphore = asyncio.Semaphore(max(1, concurrency))
    # Budget admission: serialized, and each in-flight call reserves the
    # largest observed per-call cost so far. The first wave (no observations
    # yet) can still overshoot by up to `concurrency` calls; every wave after
    # that is bounded by the observed cost.
    admission = asyncio.Lock()
    observed_costs: List[float] = []
    reserved_total = 0.0
    resolved_model_id = model_id or _agent_model_id(agent)
    start_total = ledger.total if ledger is not None else 0.0

    outputs: List[ForecastOutput] = []
    errors: List[str] = []
    skipped = 0

    async def run_one(question: ForecastQuestion) -> Optional[ForecastOutput]:
        nonlocal skipped, reserved_total
        async with semaphore:
            reserved = 0.0
            if budget is not None:
                async with admission:
                    estimate = max(observed_costs) if observed_costs else 0.0
                    remaining = budget.remaining()
                    if budget.exceeded() or (remaining is not None and remaining <= reserved_total + estimate):
                        skipped += 1
                        return None
                    reserved = estimate
                    reserved_total += reserved
            try:
                output = await agent.run(question)
            except Exception as exc:  # noqa: BLE001 - surfaced in the batch result
                errors.append(f"{question.id}: {exc}")
                return None
            finally:
                if budget is not None:
                    async with admission:
                        reserved_total = max(0.0, reserved_total - reserved)
            if ledger is not None:
                call_start = ledger.total
                try:
                    ledger.record_output(resolved_model_id, output)
                except Exception as exc:  # noqa: BLE001 - pricing must never discard a forecast
                    logger.warning("Ledger could not price output for %s: %s", question.id, exc)
                    ledger.record_unpriced(resolved_model_id, getattr(output, "usage", None), str(exc))
                observed_costs.append(max(0.0, ledger.total - call_start))
            return output

    results = await asyncio.gather(*(run_one(question) for question in questions))
    outputs = [result for result in results if result is not None]

    batch_cost = (ledger.total - start_total) if ledger is not None else 0.0
    return BatchForecastResult(
        outputs=outputs,
        errors=errors,
        skipped=skipped,
        cost=batch_cost,
        currency=ledger.price_table.currency if ledger is not None else "",
    )
