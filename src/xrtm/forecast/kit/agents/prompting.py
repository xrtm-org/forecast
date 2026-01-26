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
Structured prompting and compiled agents for Phase 7 optimization.
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from xrtm.forecast.providers.inference.base import InferenceProvider

from .llm import LLMAgent

logger = logging.getLogger(__name__)


class PromptTemplate(BaseModel):
    r"""
    A structured prompt template that can be optimized by a compiler.

    Attributes:
        instruction (`str`): The core system instruction or persona.
        examples (`List[Dict[str, str]]`): Few-shot examples for the LLM.
        version (`int`): Incremental version for optimization tracking.
    """

    instruction: str
    examples: List[Dict[str, str]] = Field(default_factory=list)
    version: int = 1


class CompiledAgent(LLMAgent):
    r"""
    An LLM agent that uses a versioned PromptTemplate.
    This allows an optimizer to modify the template to improve performance.
    """

    def __init__(self, model: InferenceProvider, template: PromptTemplate, name: Optional[str] = None):
        super().__init__(model, name)
        self.template = template

    def _render_prompt(self, input_text: str) -> str:
        r"""Combines template instruction, examples, and input into a single prompt."""
        prompt = f"SYSTEM: {self.template.instruction}\n\n"
        if self.template.examples:
            prompt += "EXAMPLES:\n"
            for ex in self.template.examples:
                prompt += f"Input: {ex.get('input')}\nOutput: {ex.get('output')}\n---\n"

        prompt += f"\nUSER: {input_text}\n"
        return prompt

    async def run(self, input_data: Any, **kwargs) -> Any:
        r"""Executes the agent using the current prompt template."""
        prompt = self._render_prompt(str(input_data))
        response = await self.model.generate(prompt)
        return response


__all__ = ["PromptTemplate", "CompiledAgent"]
