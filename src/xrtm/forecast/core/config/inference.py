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
    timeout: int = Field(
        default=120,
        description="Request timeout in seconds. Reasoning models can spend minutes in "
        "chain-of-thought before emitting content; the old 30s default was too low for them.",
    )
    extra: Dict[str, Any] = Field(default_factory=dict)


class OpenAIConfig(ProviderConfig):
    r"""Specific configuration for OpenAI or compatible backends.

    Args:
        max_retries: Maximum retry attempts for transient API errors (default 2).
        backoff_base: Base for exponential backoff in seconds (default 2.0).
    """

    base_url: str = "https://api.openai.com/v1"
    max_retries: int = Field(default=2, ge=0, description="Maximum retry attempts for transient API errors")
    backoff_base: float = Field(default=2.0, gt=1.0, description="Base for exponential backoff in seconds")
    retry_on_empty_content: bool = Field(
        default=True,
        description="Retry once with a larger max_tokens when a reasoning model returns empty content.",
    )
    empty_content_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        le=4.0,
        description="max_tokens multiplier applied to the empty-content retry.",
    )
    cache_ttl_seconds: Optional[int] = Field(
        default=None,
        ge=0,
        description="Optional TTL for cached responses. None keeps entries until LRU/size eviction.",
    )
    cache_non_deterministic: bool = Field(
        default=False,
        description="Cache responses even when temperature > 0. Off by default so sampling is not silently frozen.",
    )
    rate_limit_timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        description="How long a request waits for a rate-limit token before failing.",
    )
    redis_url: Optional[str] = Field(
        default=None,
        description="Optional Redis URL for cross-process rate limiting (in-memory fallback otherwise).",
    )
    thinking: str = Field(
        default="auto",
        pattern="^(auto|enabled|disabled)$",
        description="Reasoning/thinking mode for reasoning-capable models. 'auto' keeps the provider "
        "default; 'enabled'/'disabled' send extra_body {'thinking': {'type': ...}} (DeepSeek-compatible).",
    )
