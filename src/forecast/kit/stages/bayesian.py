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
Bayesian Sieve Stage.
A Graph node that updates a probability prior using a Bayes Factor (Likelihood Ratio)
provided by an agent.
r"""

import logging
from typing import Optional

from forecast.core.eval.bayesian import bayesian_update
from forecast.core.schemas.graph import BaseGraphState
from forecast.kit.agents.base import Agent

logger = logging.getLogger(__name__)


class BayesianSieveStage:
    r"""
    A Graph Stage that performs a Bayesian update on a numerical prior.

    Instead of an agent guessing a probability directly, it provides a
    Likelihood Ratio (Bayes Factor) based on specific evidence. The stage
    then performs the mathematical update.

    Example:
        ```python
        stage = BayesianSieveStage(
            agent=my_agent,
            prior_key="base_rate",
            output_key="updated_forecast"
        )
        ```
    r"""

    def __init__(
        self,
        agent: Agent,
        prior_key: str = "prior",
        output_key: str = "posterior",
        evidence_prompt: Optional[str] = None,
    ):
        r"""
        Initializes the BayesianSieveStage.

        Args:
            agent (`Agent`):
                The agent responsible for calculating the Likelihood Ratio (Bayes Factor).
            prior_key (`str`, *optional*, defaults to `"prior"`):
                The key in `state.context` where the prior probability is stored.
            output_key (`str`, *optional*, defaults to `"posterior"`):
                The key where the resulting posterior probability will be saved.
            evidence_prompt (`str`, *optional*):
                A specific prompt instructions for the agent to focus on evidence.
        r"""
        self.agent = agent
        self.prior_key = prior_key
        self.output_key = output_key
        self.evidence_prompt = evidence_prompt

    async def __call__(self, state: BaseGraphState) -> BaseGraphState:
        r"""
        Executes the Bayesian update.

        Args:
            state (`BaseGraphState`):
                The current graph state.

        Returns:
            `BaseGraphState`: The updated graph state.
        r"""
        prior = state.context.get(self.prior_key)
        if prior is None:
            logger.warning(f"Prior key '{self.prior_key}' not found in state context. Defaulting to 0.5.")
            prior = 0.5

        # 1. Ask agent for Bayes Factor
        # In a real implementation, we'd have a specific protocol for Likelihood Ratios.
        # For now, we simulate this via a structured call to the agent.
        prompt = self.evidence_prompt or "Analyze the evidence and provide a Likelihood Ratio (Bayes Factor)."

        # We expect the agent to return a numerical value in its response or metadata.
        # For this v0.3.0 prototype, we use a simple run call.
        agent_result = await self.agent.run(prompt, context=state.context)

        # We look for 'bayes_factor' in the agent's structured output or metadata
        bf = agent_result.metadata.get("bayes_factor")

        if bf is None:
            # Fallback parsing logic if metadata is missing
            logger.warning("Agent did not return a 'bayes_factor' in metadata. Falling back to 1.0.")
            bf = 1.0

        # 2. Perform Math Update
        posterior = bayesian_update(float(prior), float(bf))

        # 3. Update State
        state.context[self.output_key] = posterior

        # Use output_key as the report identifier to avoid dependency on orchestrator node naming
        state.node_reports[self.output_key] = {
            "prior": prior,
            "bayes_factor": bf,
            "posterior": posterior,
            "agent_info": self.agent.get_info(),
        }

        return state


__all__ = ["BayesianSieveStage"]
