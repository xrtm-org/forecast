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

r"""Mock inference provider for testing.

Hash-derived probabilities — zero cost, no API keys, deterministic output.
Used for CI smoke tests and local pipeline validation.
"""

from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace
from typing import Any

from xrtm.forecast.providers.inference.base import InferenceProvider, ModelResponse


class MockProvider(InferenceProvider):
    """Hash-derived provider for CI smoke testing — zero cost, no API key.

    Args:
        seed: Optional integer seed for varied but reproducible probability
            mappings. Same prompt + same seed = same output. Different seeds
            produce different output. Omit for existing behavior.
    """

    model_id = "xrtm-mock"
    base_url = "mock://"
    supports_tools = False

    def __init__(self, seed: int | None = None) -> None:
        self._cache: dict[str, ModelResponse] = {}
        self._seed = seed

    def _make_key(self, prompt: Any) -> str:
        payload = json.dumps(prompt, sort_keys=True, default=str)
        if self._seed is not None:
            payload = f"{self._seed}:{payload}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def generate_content(self, prompt: Any, **kwargs: Any) -> ModelResponse:
        key = self._make_key(prompt)
        if key in self._cache:
            return self._cache[key]
        bucket = int(key[:8], 16) / 0xFFFFFFFF
        p = round(0.05 + bucket * 0.9, 3)
        text = json.dumps({"probability": p, "reasoning": "mock", "causal_nodes": [], "causal_edges": []})
        resp = ModelResponse(text=text, raw=SimpleNamespace(), usage={"total_tokens": 2}, metadata={"mock": True})
        self._cache[key] = resp
        return resp

    async def generate_content_async(self, prompt: Any, **kwargs: Any) -> ModelResponse:
        return self.generate_content(prompt, **kwargs)

    async def stream(self, messages, **kwargs: Any):
        yield self.generate_content(messages, **kwargs)


__all__ = ["MockProvider"]
