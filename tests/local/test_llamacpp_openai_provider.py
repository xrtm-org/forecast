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

import os
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest
from pydantic import SecretStr

from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.providers.inference.factory import ModelFactory


def _local_base_url() -> str:
    return os.getenv("XRTM_LOCAL_LLM_BASE_URL", "http://localhost:8080/v1").rstrip("/")


def _health_url(base_url: str) -> str:
    if base_url.endswith("/v1"):
        return base_url[:-3] + "/health"
    return base_url.rstrip("/") + "/health"


def _require_local_llm(base_url: str) -> None:
    request = Request(_health_url(base_url), method="GET")
    try:
        with urlopen(request, timeout=2) as response:
            if response.status != 200:
                pytest.fail(f"Local LLM endpoint returned HTTP {response.status}")
    except URLError as exc:
        pytest.fail(f"Local LLM endpoint is not reachable at {base_url}: {exc}")


@pytest.mark.local_llm
def test_llamacpp_openai_compatible_provider_smoke() -> None:
    r"""Smoke-test the local llama.cpp server through the OpenAI-compatible provider."""
    base_url = _local_base_url()
    _require_local_llm(base_url)

    config = OpenAIConfig(
        model_id=os.getenv("XRTM_LOCAL_LLM_MODEL", "Qwen3.5-9B-UD-Q4_K_XL.gguf"),
        api_key=SecretStr(os.getenv("XRTM_LOCAL_LLM_API_KEY", "test")),
        base_url=base_url,
    )
    provider = ModelFactory.get_provider(config)
    max_tokens = int(os.getenv("XRTM_LOCAL_LLM_MAX_TOKENS", "512"))

    response = provider.generate_content(
        "Reply with exactly XRTM_LOCAL_OK and no other text.",
        max_tokens=max_tokens,
        temperature=0,
    )

    assert "XRTM_LOCAL_OK" in response.text
    assert response.usage["total_tokens"] > 0
