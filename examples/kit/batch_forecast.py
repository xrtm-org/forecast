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

r"""Batch-forecast several questions with MockProvider and a cost ledger.

Run: python examples/kit/batch_forecast.py
"""

import asyncio

from xrtm.data.core.schemas.forecast import ForecastQuestion

from xrtm.forecast.core.policies import DEEPSEEK_CNY_PRICES, CostLedger
from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from xrtm.forecast.kit.batch import forecast_many
from xrtm.forecast.providers.inference.mock_provider import MockProvider


async def main() -> None:
    analyst = ForecastingAnalyst(model=MockProvider(), name="batch-demo")
    questions = [ForecastQuestion(id=f"q{i}", title=f"Will event {i} happen?") for i in range(5)]

    ledger = CostLedger(DEEPSEEK_CNY_PRICES)
    result = await forecast_many(analyst, questions, concurrency=3, ledger=ledger)

    print(f"{len(result.outputs)} forecasts, {result.skipped} skipped, {len(result.errors)} errors")
    for output in result.outputs:
        print(f"  {output.forecast_request_id}: p={output.probability:.2f} parse={output.parse_status}")
    print(f"cost: {result.cost:.4f} {result.currency}")


if __name__ == "__main__":
    asyncio.run(main())
