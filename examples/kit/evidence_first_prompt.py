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

r"""Forecast one question with the evidence-first prompt preset.

Run: python examples/kit/evidence_first_prompt.py

The question carries a numeric reference value in its context. With a neutral
system prompt, forecasters tend to anchor on that number; the evidence-first
preset forces an independent estimate first, then a reasoned reconciliation.
"""

import asyncio

from xrtm.data.core.schemas.forecast import ForecastQuestion

from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst
from xrtm.forecast.kit.prompts import evidence_first_template
from xrtm.forecast.providers.inference.mock_provider import MockProvider


async def main() -> None:
    question = ForecastQuestion(
        id="demo-1",
        title="Will the central bank cut rates at the next meeting?",
        description="Reference scenario for the evidence-first prompt pattern.",
        context={"reference_value": 0.35},
    )
    analyst = ForecastingAnalyst(
        model=MockProvider(),
        name="evidence-first-demo",
        prompt_template=evidence_first_template(),
    )
    output = await analyst.run(question)
    print(f"prompt_id:  {analyst.prompt_id}")
    print(f"probability: {output.probability}")
    print("Swap MockProvider for a live provider to observe the anchoring effect.")


if __name__ == "__main__":
    asyncio.run(main())
