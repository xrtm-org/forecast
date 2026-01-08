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

from typing import Any, Type

import pytest
from pydantic import SecretStr

from forecast.inference.base import InferenceProvider
from forecast.inference.config import GeminiConfig, HFConfig, OpenAIConfig
from forecast.inference.gemini_provider import GeminiProvider
from forecast.inference.hf_provider import HuggingFaceProvider
from forecast.inference.openai_provider import OpenAIProvider


@pytest.mark.parametrize(
    "provider_class, config_class, model_id",
    [
        (GeminiProvider, GeminiConfig, "gemini-2.0-flash"),
        (OpenAIProvider, OpenAIConfig, "gpt-4o"),
        (HuggingFaceProvider, HFConfig, "sshleifer/tiny-gpt2"),
    ],
)
class TestProviderConformance:
    r"""
    Unified conformance suite for all InferenceProvider implementations.
    Ensures that every provider adheres to the "Institutional Grade" interface.
    """

    def test_structural_conformance(self, provider_class: Type[InferenceProvider], config_class: Any, model_id: str):
        r"""Verifies that the provider implements the required interface."""
        cfg = config_class(model_id=model_id, api_key=SecretStr("mock"))

        # HuggingFace might fail on init if libraries missing, we catch it
        try:
            provider = provider_class(cfg)  # type: ignore[call-arg]
        except ImportError:
            pytest.skip("Provider dependencies not installed.")

        assert hasattr(provider, "generate_content_async")
        assert hasattr(provider, "generate_content")
        assert hasattr(provider, "stream")
        assert hasattr(provider, "run")
        assert isinstance(provider.supports_tools, bool)

    @pytest.mark.asyncio
    async def test_run_alias(self, provider_class: Type[InferenceProvider], config_class: Any, model_id: str):
        r"""Verifies that the ergonomic .run() alias exists (logic check)."""
        # We don't actually call the network here, just check the method exists and is async
        import inspect
        assert inspect.iscoroutinefunction(provider_class.run)

    def test_docstring_institutional_standard(self, provider_class: Type[InferenceProvider], config_class: Any, model_id: str):
        r"""Verifies that public methods have Hugging Face style docstrings."""
        methods = ["generate_content_async", "generate_content", "stream"]
        for m_name in methods:
            method = getattr(provider_class, m_name)
            doc = method.__doc__
            assert doc is not None, f"Method {m_name} is missing a docstring."
            assert "Args" in doc, f"Method {m_name} docstring is missing 'Args' section."
            assert "Returns" in doc, f"Method {m_name} docstring is missing 'Returns' section."
