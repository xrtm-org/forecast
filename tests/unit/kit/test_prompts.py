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

r"""Tests for the evidence-first prompt preset."""

from xrtm.forecast.core.schemas.prompt import PromptTemplate
from xrtm.forecast.kit.prompts import EVIDENCE_FIRST_SYSTEM_PROMPT, evidence_first_template


def test_evidence_first_template_defaults():
    template = evidence_first_template()
    assert isinstance(template, PromptTemplate)
    assert template.prompt_id == "evidence-first-v1"
    assert "FIRST derive an independent probability" in template.system_prompt
    assert "reference value" in template.system_prompt
    assert "Output valid JSON" in template.system_prompt


def test_evidence_first_template_custom_id_and_extra():
    template = evidence_first_template(prompt_id="custom-v2", extra_instructions="Extra: cite sources.")
    assert template.prompt_id == "custom-v2"
    assert template.system_prompt.endswith("Extra: cite sources.")
    assert EVIDENCE_FIRST_SYSTEM_PROMPT in template.system_prompt


def test_evidence_first_prompt_is_domain_agnostic():
    # xrtm core/kit must avoid financial jargon (governance rule)
    lowered = EVIDENCE_FIRST_SYSTEM_PROMPT.lower()
    for term in ("market price", "kelly", "payout", "trade", "portfolio"):
        assert term not in lowered
