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

    model_id: str = Field(..., description="The unique identifier for the model (e.g. 'gpt-4o')")
    api_key: Optional[SecretStr] = Field(
        default=None,
        description="API key for the provider. If None, it will be pulled from environment.",
    )
    rpm: int = 15
    timeout: int = 30
    extra: Dict[str, Any] = Field(default_factory=dict)


class GeminiConfig(ProviderConfig):
    """Specific configuration for Google Gemini."""

    redis_url: Optional[str] = None


class OpenAIConfig(ProviderConfig):
    """Specific configuration for OpenAI or compatible backends."""

    base_url: str = "https://api.openai.com/v1"


class HFConfig(ProviderConfig):
    """Configuration for local Hugging Face models."""

    device: str = "cpu"  # cpu, cuda, mps
    quantization: Optional[str] = None  # 4bit, 8bit
    trust_remote_code: bool = False
    cache_dir: Optional[str] = None


class VLLMConfig(ProviderConfig):
    """Configuration for vLLM high-throughput local serving."""

    tensor_parallel_size: int = 1
    gpu_memory_utilization: float = 0.9
    max_model_len: Optional[int] = None


class XLMConfig(HFConfig):
    """Specific configuration for XLM (Local Encoder) specialists."""

    use_fast_tokenizer: bool = True
