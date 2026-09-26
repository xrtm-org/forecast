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

r"""Implement a minimal InferenceProvider and use it with ForecastingAnalyst.

Run: python examples/providers/custom_provider.py
"""

import asyncio
import json
from typing import Any

from xrtm.forecast.core.interfaces import InferenceProvider, ModelResponse
from xrtm.forecast.kit.agents.specialists.analyst import ForecastingAnalyst


class StaticForecastProvider(InferenceProvider):
    r"""Provider that returns a fixed, well-formed JSON forecast payload."""

    model_id = "static-demo"

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        payload = {
            "probability": 0.63,
            "confidence_interval": {"low": 0.53, "high": 0.73, "level": 0.9},
            "reasoning": "Static demo provider.",
            "causal_nodes": [{"node_id": "n1", "event": "demo", "probability": 0.63}],
            "causal_edges": [],
        }
        return ModelResponse(
            text=json.dumps(payload),
            usage={"prompt_tokens": 12, "completion_tokens": 24, "total_tokens": 36},
        )

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        return self.generate_content(prompt, output_logprobs, **kwargs)

    async def stream(self, messages: Any, **kwargs: Any):
        yield self.generate_content("")


async def main() -> None:
    analyst = ForecastingAnalyst(model=StaticForecastProvider(), prompt_id="static-demo-v1")
    output = await analyst.run("Will the demo parse cleanly?")

    print(f"p={output.probability:.2f} parse_status={output.parse_status}")
    if output.provenance:
        print(f"model={output.provenance.model_id} prompt_id={output.provenance.prompt_id}")
    print(f"usage={output.usage.model_dump()}")


if __name__ == "__main__":
    asyncio.run(main())
