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
BrierOptimizer for automated prompt engineering.
"""

import logging
from typing import Any, List, Tuple

from forecast.kit.agents.prompting import CompiledAgent, PromptTemplate

logger = logging.getLogger(__name__)


class BrierOptimizer:
    r"""
    A simple "Teleprompter" that optimizes an agent's prompt template
    to minimize Brier Score based on historical failures.
    """

    def __init__(self, optimizer_model: Any):
        self.optimizer_model = optimizer_model

    async def optimize(self, agent: CompiledAgent, dataset: List[Tuple[Any, float, int]]) -> PromptTemplate:
        r"""
        Analyzes performance and suggests an improved prompt template.

        Args:
            agent (`CompiledAgent`): The agent to optimize.
            dataset (`List[Tuple[input, prediction, ground_truth]]`):
                Training data for the optimizer.
        """
        # 1. Collect statistics
        total_error = sum((p - g) ** 2 for _, p, g in dataset) / len(dataset)

        # 2. Format a request to the meta-optimizer LLM
        # This is a prototype of the DSPy "BootstrappedFewShot" or "MIPRO" approach
        meta_prompt = f"""
        You are a Prompt Optimizer for a forecasting engine.
        Current Goal: Minimize Brier Score (Current: {total_error:.4f}).

        Current Instruction: "{agent.template.instruction}"

        Performance Snippets (Input -> Pred vs Truth):
        """
        for inp, pred, truth in dataset[:5]:
            meta_prompt += f"- {str(inp)[:50]}... -> {pred} (Actual: {truth})\n"

        meta_prompt += """
        Suggest a NEW system instruction that corrects for these errors.
        If the agent is too confident, tell it to be more cautious.
        Return ONLY the new instruction string.
        """

        new_instruction = await self.optimizer_model.generate(meta_prompt)

        # 3. Create a new template
        return PromptTemplate(
            instruction=new_instruction.strip(), examples=agent.template.examples, version=agent.template.version + 1
        )


__all__ = ["BrierOptimizer"]
