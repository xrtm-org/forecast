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

r"""Lightweight model capability registry.

Describes what each known model can do (thinking mode, JSON mode, tools,
context limits) so providers and agents can make capability-aware decisions
without hard-coding model names everywhere.

Example:
    >>> from xrtm.forecast.core.config.models import get_model_spec
    >>> get_model_spec("deepseek-flash").supports_thinking
    True
"""

from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field

__all__ = [
    "ModelSpec",
    "get_model_spec",
    "register_model_spec",
]


class ModelSpec(BaseModel):
    r"""Capability description for one model.

    Attributes:
        model_id: The model identifier as requested from the provider.
        provider: Provider family (e.g. ``"deepseek"``, ``"openai"``).
        context_window: Maximum context window in tokens, if known.
        max_output_tokens: Maximum output tokens, if known.
        supports_thinking: Whether the model supports a thinking/reasoning mode.
        supports_json_mode: Whether the model supports provider-enforced JSON output.
        supports_tools: Whether the model supports tool/function calling.
        notes: Free-form operational notes.
    """

    model_id: str = Field(..., description="Model identifier as requested from the provider")
    provider: str = Field(default="openai-compatible", description="Provider family")
    context_window: Optional[int] = Field(default=None, description="Maximum context window in tokens")
    max_output_tokens: Optional[int] = Field(default=None, description="Maximum output tokens")
    supports_thinking: bool = Field(default=False, description="Whether a thinking/reasoning mode is supported")
    supports_json_mode: bool = Field(default=False, description="Whether provider-enforced JSON output is supported")
    supports_tools: bool = Field(default=True, description="Whether tool/function calling is supported")
    notes: str = Field(default="", description="Free-form operational notes")


_DEEPSEEK_FLASH = ModelSpec(
    model_id="deepseek-flash",
    provider="deepseek",
    context_window=1_048_576,
    max_output_tokens=393_216,
    supports_thinking=True,
    supports_json_mode=True,
    notes="DeepSeek V4.1-Flash. Legacy aliases deepseek-chat and deepseek-v4-flash route here.",
)

_DEEPSEEK_PRO = ModelSpec(
    model_id="deepseek-v4-pro",
    provider="deepseek",
    context_window=1_048_576,
    max_output_tokens=393_216,
    supports_thinking=True,
    supports_json_mode=True,
    notes="DeepSeek V4-Pro (reasoning).",
)

_GENERIC = ModelSpec(
    model_id="default",
    provider="openai-compatible",
    supports_thinking=False,
    supports_json_mode=False,
    notes="Unknown model; conservative capabilities.",
)

_MODEL_REGISTRY: Dict[str, ModelSpec] = {
    "deepseek-flash": _DEEPSEEK_FLASH,
    "deepseek-chat": _DEEPSEEK_FLASH,
    "deepseek-v4-flash": _DEEPSEEK_FLASH,
    "deepseek-v4-pro": _DEEPSEEK_PRO,
}


def get_model_spec(model_id: str) -> ModelSpec:
    r"""Return the :class:`ModelSpec` for *model_id*, falling back to a generic spec."""
    return _MODEL_REGISTRY.get(model_id, _GENERIC) if model_id else _GENERIC


def register_model_spec(spec: ModelSpec) -> None:
    r"""Register or override a model spec in the process-local registry."""
    _MODEL_REGISTRY[spec.model_id] = spec
