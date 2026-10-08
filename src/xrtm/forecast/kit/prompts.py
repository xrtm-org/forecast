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

r"""Reusable prompt presets for forecasting agents.

**Evidence-first (anti-anchoring).** Forecasters shown a numeric reference value
(a market price, poll, or consensus estimate) in the prompt tend to anchor on
it. In a paired A/B on a prediction-market pool, a neutral system prompt
produced a mean absolute deviation of 0.5c from the reference, the
evidence-first instruction below produced 6.4c, and withholding the reference
produced 29c. Forcing the model to *commit to an evidence-based estimate first*
restored most of the independence while keeping the reference available as
information.

Use :func:`evidence_first_template` whenever a numeric anchor appears in the
question context.

Example:
    >>> from xrtm.forecast.kit.prompts import evidence_first_template
    >>> template = evidence_first_template()
    >>> template.prompt_id
    'evidence-first-v1'
"""

from __future__ import annotations

from xrtm.forecast.core.schemas.prompt import PromptTemplate

__all__ = ["EVIDENCE_FIRST_SYSTEM_PROMPT", "evidence_first_template"]

EVIDENCE_FIRST_SYSTEM_PROMPT = """\
You are a calibrated probabilistic forecaster. Estimate the probability of the \
event described in the question.

Method (follow strictly, in order):
1. FIRST derive an independent probability from base rates, historical patterns, \
and the specific evidence provided. Commit to this estimate before you consider \
any numeric reference value included in the context.
2. Only then compare your estimate with the reference value, if one is provided.
3. Keep your independent estimate unless you can state a specific, evidence-based \
reason the reference is better informed. Do not move toward the reference merely \
because it exists — a forecast that restates a reference value has no value.
4. If you are highly uncertain, say so: use a probability near 0.50 with a wide \
confidence interval. It is better to say "I don't know" than to be confidently wrong.
5. Do not fabricate information. If the available evidence is insufficient, widen \
your confidence interval rather than guessing.
6. Output valid JSON matching the required schema — no markdown, no commentary \
outside it."""


def evidence_first_template(prompt_id: str = "evidence-first-v1", extra_instructions: str = "") -> PromptTemplate:
    r"""Build the evidence-first :class:`PromptTemplate`.

    Args:
        prompt_id: Identifier recorded in the forecast provenance.
        extra_instructions: Optional domain-specific text appended to the method.

    Returns:
        A :class:`PromptTemplate` whose ``system_prompt`` forces an independent
        estimate before any numeric reference value is considered.

    Example:
        >>> from xrtm.forecast.kit.prompts import evidence_first_template
        >>> template = evidence_first_template(prompt_id="trading-v1")
        >>> template.prompt_id
        'trading-v1'
    """
    system_prompt = EVIDENCE_FIRST_SYSTEM_PROMPT
    if extra_instructions:
        system_prompt = f"{system_prompt}\n\n{extra_instructions}"
    return PromptTemplate(
        prompt_id=prompt_id,
        system_prompt=system_prompt,
        notes="Evidence-first: commit to an independent estimate before considering any numeric reference value.",
    )
