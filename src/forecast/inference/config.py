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

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, SecretStr


class ProviderConfig(BaseModel):
    """Base configuration for any inference provider."""

    model_id: str
    api_key: Optional[SecretStr] = None
    rpm: int = 15
    timeout: int = 30
    extra: Dict[str, Any] = Field(default_factory=dict)


class GeminiConfig(ProviderConfig):
    """Specific configuration for Google Gemini."""

    use_cheap_models: bool = True
    flash_model_id: str = "gemini-2.0-flash-lite"
    smart_model_id: str = "gemini-2.0-flash"
    redis_url: Optional[str] = "redis://localhost:6379"


class OpenAIConfig(ProviderConfig):
    """Specific configuration for OpenAI or compatible backends."""

    base_url: str = "https://api.openai.com/v1"
