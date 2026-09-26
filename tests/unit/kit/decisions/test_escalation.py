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

r"""Tests for decision escalation routing."""

from typing import Any, Dict, Optional, Sequence

import pytest

from xrtm.forecast.core.interfaces import DecisionProvider
from xrtm.forecast.core.schemas.decision import DecisionOption, DecisionResult
from xrtm.forecast.kit.decisions import EscalationRouter

OPTIONS = [DecisionOption(name="trade"), DecisionOption(name="skip")]


class StaticDecisionProvider(DecisionProvider):
    r"""Decision provider that always returns a fixed result and records calls."""

    def __init__(self, result: DecisionResult):
        self.result = result
        self.contexts: list[Optional[Dict[str, Any]]] = []

    async def decide(
        self,
        state: str,
        options: Sequence[DecisionOption],
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> DecisionResult:
        self.contexts.append(context)
        return self.result.model_copy(deep=True)


@pytest.mark.asyncio
async def test_high_confidence_does_not_escalate():
    primary = StaticDecisionProvider(DecisionResult(decision="trade", confidence=0.95))
    fallback = StaticDecisionProvider(DecisionResult(decision="skip", confidence=0.99))

    result = await EscalationRouter(primary, fallback, confidence_threshold=0.7).decide("state", OPTIONS)

    assert result.decision == "trade"
    assert result.escalated is False
    assert fallback.contexts == []


@pytest.mark.asyncio
async def test_low_confidence_escalates_with_draft_context():
    primary = StaticDecisionProvider(DecisionResult(decision="trade", confidence=0.4))
    fallback = StaticDecisionProvider(DecisionResult(decision="skip", confidence=0.9))

    result = await EscalationRouter(primary, fallback, confidence_threshold=0.7).decide("state", OPTIONS)

    assert result.decision == "skip"
    assert result.escalated is True
    assert fallback.contexts[0] is not None
    assert fallback.contexts[0]["draft_decision"]["decision"] == "trade"


@pytest.mark.asyncio
async def test_escalate_flag_triggers_fallback():
    primary = StaticDecisionProvider(DecisionResult(decision="trade", confidence=0.9, escalate=True))
    fallback = StaticDecisionProvider(DecisionResult(decision="skip", confidence=0.9))

    result = await EscalationRouter(primary, fallback, confidence_threshold=0.7).decide("state", OPTIONS)

    assert result.decision == "skip"
    assert result.escalated is True


@pytest.mark.asyncio
async def test_without_fallback_returns_primary_result():
    primary = StaticDecisionProvider(DecisionResult(decision="trade", confidence=0.1))

    result = await EscalationRouter(primary, fallback=None, confidence_threshold=0.7).decide("state", OPTIONS)

    assert result.decision == "trade"
    assert result.escalated is False
