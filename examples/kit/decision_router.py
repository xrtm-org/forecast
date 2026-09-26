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

r"""Route a decision through a cheap provider with LLM escalation.

Run: python examples/kit/decision_router.py
"""

import asyncio
from typing import Any, Dict, Optional, Sequence

from xrtm.forecast.core.interfaces import DecisionProvider
from xrtm.forecast.core.schemas.decision import DecisionOption, DecisionResult
from xrtm.forecast.kit.decisions import EscalationRouter


class LowConfidenceDecision(DecisionProvider):
    r"""Cheap provider that is only confident half the time."""

    async def decide(
        self,
        state: str,
        options: Sequence[DecisionOption],
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> DecisionResult:
        return DecisionResult(decision=options[0].name, confidence=0.4)


class CarefulDecision(DecisionProvider):
    r"""Stronger fallback used when the cheap provider is uncertain."""

    async def decide(
        self,
        state: str,
        options: Sequence[DecisionOption],
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> DecisionResult:
        draft = (context or {}).get("draft_decision", {})
        return DecisionResult(decision=draft.get("decision", options[-1].name), confidence=0.9)


async def main() -> None:
    router = EscalationRouter(
        primary=LowConfidenceDecision(),
        fallback=CarefulDecision(),
        confidence_threshold=0.7,
    )
    options = [DecisionOption(name="trade", description="Open a position"), DecisionOption(name="skip")]

    result = await router.decide("Market looks mispriced at 0.42.", options)
    print(f"decision={result.decision} confidence={result.confidence:.2f} escalated={result.escalated}")


if __name__ == "__main__":
    asyncio.run(main())
