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

import pytest
from pydantic import SecretStr

from xrtm.forecast.core.cache import InferenceCache
from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.providers.inference.factory import ModelFactory
from xrtm.forecast.providers.inference.openai_provider import OpenAIProvider


def test_model_factory_env_profiles(monkeypatch):
    r"""Verifies that Environment Profiles correctly influence model selection."""
    monkeypatch.setenv("OPENAI_API_KEY", "mock-key")

    # Dev Profile (OpenAI)
    p_dev_oa = ModelFactory.get_provider("openai", env="dev")
    assert p_dev_oa.config.model_id == "gpt-4o-mini"

    # Production Profile (OpenAI)
    p_prod_oa = ModelFactory.get_provider("openai", env="production")
    assert p_prod_oa.config.model_id == "gpt-4o"

    # Explicit model_id is overridden by env profile
    p_explicit = ModelFactory.get_provider("openai", model_id="gpt-3.5-turbo", env="production")
    assert p_explicit.config.model_id == "gpt-4o"


def test_model_factory_preserves_provider_runtime_kwargs(tmp_path):
    cache = InferenceCache(db_path=str(tmp_path / "cache.db"))
    config = OpenAIConfig(model_id="gpt-4o-mini", api_key=SecretStr("mock-key"))

    provider = ModelFactory.get_provider(config, cache=cache)

    assert isinstance(provider, OpenAIProvider)
    assert provider.cache is cache
    cache.close()
