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
Red Team Agent: Adversarial Counter-Argument Generator.

Implements the "Devil's Advocate" pattern from the SOTA strategies to combat
groupthink and sycophancy in consensus topologies. The Red Team Agent is
*ordered* to argue against a given thesis, forcing the supervisor to consider
opposing viewpoints.

Example:
    ```python
    >>> red_team = RedTeamAgent(model=llm)
    >>> counter = await red_team.challenge(
    ...     thesis="The Fed will raise rates (80% confidence)",
    ...     reasoning="Strong employment data..."
    ... )
    >>> print(counter.counter_argument)
    "However, inflation is already declining..."
    ```
"""

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from xrtm.forecast.core.interfaces import InferenceProvider

from .base import Agent

logger = logging.getLogger(__name__)


class CounterArgument(BaseModel):
    r"""
    The structured output of a Red Team challenge.

    Attributes:
        original_thesis (`str`):
            The thesis being challenged.
        counter_argument (`str`):
            The Devil's Advocate argument against the thesis.
        weakness_points (`list[str]`):
            Specific weaknesses identified in the original reasoning.
        alternative_probability (`float`, *optional*):
            The Red Team's suggested alternative probability.
        confidence_in_challenge (`float`):
            How confident the Red Team is in the challenge (0-1).
    """

    original_thesis: str
    counter_argument: str
    weakness_points: list[str] = Field(default_factory=list)
    alternative_probability: Optional[float] = Field(None, ge=0, le=1)
    confidence_in_challenge: float = Field(default=0.5, ge=0, le=1)


class RedTeamAgent(Agent):
    r"""
    An adversarial agent that generates counter-arguments to combat groupthink.

    The Red Team Agent is designed to be integrated into consensus topologies.
    When the majority reaches a conclusion, the Red Team is *ordered* (not asked)
    to write a compelling counter-argument. This forces the final Supervisor to
    consider opposing viewpoints before making a decision.

    This pattern is inspired by real Investment Committee practices where analysts
    are assigned to write "Short theses" regardless of their personal views.

    Attributes:
        model (`InferenceProvider`):
            The LLM provider for generating counter-arguments.
        intensity (`str`):
            How aggressive the challenging should be: "mild", "moderate", "aggressive".

    Example:
        ```python
        >>> agent = RedTeamAgent(model=llm, intensity="aggressive")
        >>> result = await agent.challenge(
        ...     thesis="Rate hike is certain",
        ...     reasoning="Employment strong, inflation persistent"
        ... )
        >>> print(result.counter_argument)
        ```
    """

    def __init__(
        self,
        model: InferenceProvider,
        name: str = "RedTeam",
        intensity: str = "moderate",
    ) -> None:
        r"""
        Initializes the Red Team Agent.

        Args:
            model (`InferenceProvider`):
                The inference provider for generating challenges.
            name (`str`):
                The agent name.
            intensity (`str`):
                Challenge intensity: "mild", "moderate", or "aggressive".
        """
        super().__init__(name=name)
        self.model = model
        self.intensity = intensity

    def _build_challenge_prompt(
        self,
        thesis: str,
        reasoning: str,
        context: Optional[str] = None,
    ) -> str:
        r"""Builds the adversarial prompt based on intensity level."""
        intensity_instructions = {
            "mild": "Respectfully question the assumptions and identify potential blind spots.",
            "moderate": "Actively argue the opposing position. Find the strongest counter-evidence.",
            "aggressive": "Demolish this thesis. Find every flaw, assumption, and logical gap. Be ruthless.",
        }

        instruction = intensity_instructions.get(self.intensity, intensity_instructions["moderate"])

        prompt = f"""You are a RED TEAM ANALYST. Your job is to argue AGAINST the following thesis.

**YOUR MISSION**: {instruction}

**You are NOT asked for your opinion. You are ORDERED to find problems with this thesis.**

---

THESIS: {thesis}

SUPPORTING REASONING:
{reasoning}

{f"ADDITIONAL CONTEXT: {context}" if context else ""}

---

Respond with:
1. COUNTER_ARGUMENT: A compelling argument for why this thesis could be WRONG
2. WEAKNESSES: Bullet points of specific flaws in the reasoning (at least 3)
3. ALTERNATIVE_PROBABILITY: Your counter-estimate (just a number 0-1)
4. CHALLENGE_CONFIDENCE: How strong is your counter-argument? (0-1)

Remember: You are the Devil's Advocate. Your job is to CHALLENGE, not to agree.
"""
        return prompt

    async def challenge(
        self,
        thesis: str,
        reasoning: str,
        context: Optional[str] = None,
    ) -> CounterArgument:
        r"""
        Generates a counter-argument against the given thesis.

        Args:
            thesis (`str`):
                The position or prediction being challenged.
            reasoning (`str`):
                The supporting reasoning for the thesis.
            context (`str`, *optional*):
                Additional context (e.g., the question being forecasted).

        Returns:
            `CounterArgument`: Structured counter-argument with weaknesses.
        """
        prompt = self._build_challenge_prompt(thesis, reasoning, context)

        try:
            response = await self.model.run(prompt)
            text = response.text

            # Parse the response
            counter_arg = ""
            weaknesses: list[str] = []
            alt_prob: Optional[float] = None
            challenge_conf = 0.5

            current_section = ""
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("COUNTER_ARGUMENT:"):
                    current_section = "counter"
                    counter_arg = line.split(":", 1)[1].strip() if ":" in line else ""
                elif line.startswith("WEAKNESSES:"):
                    current_section = "weaknesses"
                elif line.startswith("ALTERNATIVE_PROBABILITY:"):
                    current_section = ""
                    try:
                        alt_prob = float(line.split(":")[1].strip())
                        alt_prob = max(0.0, min(1.0, alt_prob))
                    except (ValueError, IndexError):
                        pass
                elif line.startswith("CHALLENGE_CONFIDENCE:"):
                    current_section = ""
                    try:
                        challenge_conf = float(line.split(":")[1].strip())
                        challenge_conf = max(0.0, min(1.0, challenge_conf))
                    except (ValueError, IndexError):
                        pass
                elif current_section == "counter" and line:
                    counter_arg += " " + line
                elif current_section == "weaknesses" and line.startswith(("-", "*", "•")):
                    weaknesses.append(line.lstrip("-*• "))

            return CounterArgument(
                original_thesis=thesis,
                counter_argument=counter_arg.strip(),
                weakness_points=weaknesses,
                alternative_probability=alt_prob,
                confidence_in_challenge=challenge_conf,
            )

        except Exception as e:
            logger.error(f"[RED_TEAM] Challenge generation failed: {e}")
            return CounterArgument(
                original_thesis=thesis,
                counter_argument=f"Failed to generate challenge: {e}",
                weakness_points=[],
                alternative_probability=None,
                confidence_in_challenge=0.0,
            )

    async def run(self, input_data: Any, **kwargs: Any) -> Any:
        r"""
        Runs the Red Team agent within an orchestrator graph.

        Expects the state to contain:
        - `current_thesis`: The thesis to challenge
        - `current_reasoning`: The reasoning to challenge

        Outputs to:
        - `red_team_counter`: The CounterArgument result

        Args:
            input_data (`Any`):
                The current graph state.

        Returns:
            `Any`: Updated state with counter-argument.
        """
        state = input_data
        thesis = state.context.get("current_thesis", "")
        reasoning = state.context.get("current_reasoning", "")
        question_context = state.context.get("question_title", "")

        if not thesis:
            logger.warning("[RED_TEAM] No thesis found in state context")
            state.context["red_team_counter"] = None
            return state

        counter = await self.challenge(thesis, reasoning, question_context)
        state.context["red_team_counter"] = counter.model_dump()
        state.node_reports[self.name] = counter.counter_argument

        logger.info(f"[RED_TEAM] Challenge generated (confidence: {counter.confidence_in_challenge:.0%})")

        return state


__all__ = ["RedTeamAgent", "CounterArgument"]
