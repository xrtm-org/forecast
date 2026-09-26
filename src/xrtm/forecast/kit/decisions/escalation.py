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

r"""Decision routing helpers.

Combines a cheap/fast System-One decision provider with an optional stronger
fallback: when the primary decision is low-confidence (or explicitly asks to
escalate), the router re-asks the fallback provider and marks the result as
escalated.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from xrtm.forecast.core.interfaces import DecisionProvider
from xrtm.forecast.core.schemas.decision import DecisionOption, DecisionResult

__all__ = ["EscalationRouter"]


class EscalationRouter(DecisionProvider):
    r"""Decide with a primary provider and escalate uncertain decisions.

    Args:
        primary: The cheap/fast decision provider (e.g. Jev).
        fallback: The stronger provider (e.g. an LLM) used when escalating.
        confidence_threshold: Escalate when primary confidence is below this.
        escalate_on_flag: Also escalate when the primary sets ``escalate=True``.

    Example:
        >>> router = EscalationRouter(primary=jev, fallback=llm, confidence_threshold=0.7)  # doctest: +SKIP
        >>> result = await router.decide("state", options)  # doctest: +SKIP
    """

    def __init__(
        self,
        primary: DecisionProvider,
        fallback: Optional[DecisionProvider] = None,
        confidence_threshold: float = 0.7,
        escalate_on_flag: bool = True,
    ):
        self.primary = primary
        self.fallback = fallback
        self.confidence_threshold = confidence_threshold
        self.escalate_on_flag = escalate_on_flag

    async def decide(
        self,
        state: str,
        options: Sequence[DecisionOption],
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> DecisionResult:
        r"""Return the primary decision, escalating to the fallback when needed."""
        result = await self.primary.decide(state, options, context=context, **kwargs)

        needs_escalation = result.confidence < self.confidence_threshold
        if self.escalate_on_flag and result.escalate:
            needs_escalation = True

        if not needs_escalation or self.fallback is None:
            return result

        escalation_context = dict(context or {})
        escalation_context["draft_decision"] = result.model_dump()
        escalated = await self.fallback.decide(state, options, context=escalation_context, **kwargs)
        escalated.escalated = True
        return escalated
