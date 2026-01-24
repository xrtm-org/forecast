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

from xrtm.forecast.providers.inference.factory import ModelFactory


def test_model_factory_env_profiles(monkeypatch):
    r"""Verifies that Environment Profiles correctly influence model selection."""
    monkeypatch.setenv("OPENAI_API_KEY", "mock-key")
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")

    # 1. Dev Profile (OpenAI)
    p_dev_oa = ModelFactory.get_provider("openai", env="dev")
    assert p_dev_oa.config.model_id == "gpt-4o-mini"

    # 2. Production Profile (OpenAI)
    p_prod_oa = ModelFactory.get_provider("openai", env="production")
    assert p_prod_oa.config.model_id == "gpt-4o"

    # 3. Dev Profile (Gemini)
    p_dev_gem = ModelFactory.get_provider("gemini", env="dev")
    assert p_dev_gem.config.model_id == "gemini-2.0-flash"

    # 4. Explicit model_id should still work or be overridden?
    # Current implementation: Profiles override if provided.
    # This is standard institutional behavior for 'enforcement' of environments.
    p_explicit = ModelFactory.get_provider("openai", model_id="gpt-3.5-turbo", env="production")
    assert p_explicit.config.model_id == "gpt-4o"
