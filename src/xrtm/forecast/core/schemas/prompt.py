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

r"""Prompt templates for forecasting agents.

Templates make the persona and examples configurable data instead of code,
and give every forecast a stable ``prompt_id`` for provenance/auditing.
"""

from typing import List

from pydantic import BaseModel, Field

__all__ = ["PromptTemplate"]


class PromptTemplate(BaseModel):
    r"""A reusable forecasting prompt template.

    Attributes:
        prompt_id: Stable identifier/version recorded in forecast provenance.
        system_prompt: The system instruction block.
        few_shot_examples: Optional example strings appended to the prompt.
        notes: Free-form documentation for maintainers.
    """

    prompt_id: str = Field(default="analyst-default", description="Stable prompt identifier/version")
    system_prompt: str = Field(..., description="System instruction block for the model")
    few_shot_examples: List[str] = Field(default_factory=list, description="Optional few-shot examples")
    notes: str = Field(default="", description="Free-form documentation for maintainers")
