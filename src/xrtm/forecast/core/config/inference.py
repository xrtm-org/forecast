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

r"""Inference provider configuration schemas.

Pydantic settings for the OpenAI (and OpenAI-compatible) LLM backend,
including API keys, model identifiers, generation parameters.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, SecretStr

__all__ = [
    "ProviderConfig",
    "OpenAIConfig",
]


class ProviderConfig(BaseModel):
    r"""Base configuration for any inference provider."""

    model_id: str = Field(..., description="The unique identifier for the model (e.g. 'gpt-4o')")
    api_key: Optional[SecretStr] = Field(
        default=None,
        description="API key for the provider. If None, it will be pulled from environment.",
    )
    knowledge_cutoff: Optional[datetime] = Field(
        default=None,
        description="Optional training cutoff date for the model.",
    )
    rpm: int = 15
    timeout: int = 30
    extra: Dict[str, Any] = Field(default_factory=dict)


class OpenAIConfig(ProviderConfig):
    r"""Specific configuration for OpenAI or compatible backends."""

    base_url: str = "https://api.openai.com/v1"
