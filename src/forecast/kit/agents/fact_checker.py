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

import logging
from typing import Any, List, Optional

from forecast.core.schemas.graph import BaseGraphState
from forecast.core.tools.base import Tool
from forecast.kit.agents.base import Agent

logger = logging.getLogger(__name__)


class FactCheckerAgent(Agent):
    r"""
    An agent dedicated to verifying claims against a set of tools.

    The FactCheckerAgent:
    1. Extracts verifiable claims from the state (e.g., from `past_critique` or specific keys).
    2. Uses provided search/lookup tools to verify them.
    3. Updates the state with a 'verification_score' and 'corrected_claims'.

    Args:
        tools (`List[Tool]`):
            Tools available for verification (e.g., Search, Wikipedia).
        model_id (`str`, *optional*):
            The LLM model to use for claim extraction and verification.
    """

    def __init__(self, tools: List[Tool], model_id: str = "gemini-pro"):
        super().__init__(name="fact_checker")
        self.tools = tools
        self.model_id = model_id

    async def run(self, state: BaseGraphState, reporter: Optional[Any] = None) -> BaseGraphState:
        r"""
        Executes the fact-checking loop.

        This implementation is a simplified mock for the 'Kit' structure.
        In a full SOTA implementation, this would involve complex NLI (Natural Language Inference).
        Here, we demonstrate the architectural pattern: State -> Tool -> Update.
        """
        logger.info(f"[{self.name}] Scanning state for claims to verify...")

        # 1. Identify Claims (Mock logic for strictly typed simulation)
        # In production, this would use self.inference_provider.generate()
        claims_to_check = state.context.get("claims", [])
        if not claims_to_check:
            # Fallback: check if there is reasoning to parse
            if state.past_critique:
                claims_to_check = [state.past_critique]
            else:
                logger.info(f"[{self.name}] No claims found to verify.")
                return state

        # 2. Verify with Tools (Mock)
        # We loop through tools and try to 'search' for the claim
        verification_log = []
        for claim in claims_to_check:
            supported = False
            evidence = "No evidence found."

            # Simple heuristic: If we have tools, use them.
            # Real implementation would call tool.run()
            for tool in self.tools:
                try:
                    # We pass the claim as a query
                    result = await tool.run(temporal_context=state.temporal_context, query=f"verify: {claim}")
                    if "proven" in str(result).lower() or "verified" in str(result).lower():
                        supported = True
                        evidence = str(result)
                        break
                except Exception as e:
                    logger.warning(f"Tool {tool.name} failed: {e}")

            verification_log.append({"claim": claim, "verified": supported, "evidence": evidence})

        # 3. Update State
        state.context["fact_check_results"] = verification_log

        # Calculate a simple score
        verified_count = sum(1 for item in verification_log if item["verified"])
        score = verified_count / len(verification_log) if verification_log else 0.0
        state.context["verification_score"] = score

        if reporter:
            await reporter(0, "FactCheck", "DONE", f"Verified {len(verification_log)} claims. Score: {score:.2f}")
        return state
