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

r"""
Adversary Agent.
Specialized for Red-Team consensus and finding holes in expert reasoning.
r"""

import logging
import warnings
from typing import Any, Dict, Optional

from xrtm.forecast.kit.agents.llm import LLMAgent
from xrtm.forecast.providers.inference.base import InferenceProvider

logger = logging.getLogger(__name__)


class AdversaryAgent(LLMAgent):
    r"""
    A specialized agent designed to find flaws, biases, and contradictions
    in a collective reasoning trace.

    .. deprecated:: 0.5.0
        This class is deprecated and will be removed in v0.6.0.
        Use :class:`forecast.kit.agents.red_team.RedTeamAgent` instead,
        which provides the same functionality with a more complete API.

    The AdversaryAgent is used as a 'Red Team' in consensus topologies to
    mitigate groupthink and surface institutional risks.
    r"""

    DEFAULT_PERSONA = (
        "You are the 'Red Team' Forecaster. Your goal is NOT to agree with the experts. "
        "Your goal is to find why they are wrong. Look for:\n"
        "1. Confirmation bias.\n"
        "2. Ignored evidence.\n"
        "3. Logical leaps.\n"
        "4. Overconfidence in weak signals.\n\n"
        "Be critical, precise, and evidence-driven."
    )

    def __init__(self, model: InferenceProvider, name: Optional[str] = "TheRedTeamer", persona: Optional[str] = None):
        warnings.warn(
            "AdversaryAgent is deprecated since v0.5.0 and will be removed in v0.6.0. "
            "Use forecast.kit.agents.red_team.RedTeamAgent instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(model, name)
        self.persona = persona or self.DEFAULT_PERSONA

    async def run(self, input_data: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        r"""
        Executes the adversarial analysis.

        Args:
            input_data (`str`):
                The core question or the expert's conclusion to critique.
            context (`Dict[str, Any]`, *optional*):
                The full reasoning trace from other agents to analyze.
        r"""
        # Formulate the prompt
        experts_reasoning = context.get("expert_traces", "No trace provided.") if context else "No trace provided."

        system_prompt = self.persona
        user_prompt = (
            f"Question: {input_data}\n\n"
            f"Expert Consensus/Reasoning:\n{experts_reasoning}\n\n"
            "Identify the top 3 risks or contradictions in this reasoning."
        )

        # Call LLM
        response = await self.model.generate(
            prompt=user_prompt,
            system_instruction=system_prompt,
            temperature=0.7,  # Slight temperature for creative critique
        )

        return response


__all__ = ["AdversaryAgent"]
