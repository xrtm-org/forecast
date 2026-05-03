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

r"""Inference provider factory.

Creates and configures inference provider instances from
``Settings``, supporting automatic backend selection based on
available API keys and model identifiers.
"""

import logging
from typing import Any, Optional

from pydantic import SecretStr

from xrtm.forecast.providers.inference._policy import (
    apply_environment_profile,
    build_config,
    coerce_provider_request,
    inject_api_key_from_settings,
    instantiate_provider,
    update_config,
)
from xrtm.forecast.providers.inference.base import InferenceProvider

logger = logging.getLogger(__name__)


class ModelFactory:
    r"""
    A centralized factory for instantiating various LLM inference providers.

    `ModelFactory` decouples the creation of providers from their specific
    implementations, using `ProviderConfig` objects to drive the instantiation logic.
    r"""

    @staticmethod
    def get_provider(
        config: Optional[Any] = None,
        provider_type: Optional[str] = None,
        model_id: Optional[str] = None,
        api_key: Optional[SecretStr] = None,
        **kwargs,
    ) -> InferenceProvider:
        r"""
        Creates and returns a provider instance.

        Args:
            config (`ProviderConfig` or `str`, *optional*):
                The configuration object or a shortcut string (e.g. "gemini:gemini-2.0-flash").
            provider_type (`str`, *optional*):
                Explicitly request "GEMINI" or "OPENAI" if config is not provided.
            model_id (`str`, *optional*):
                The model identifier (e.g. "gpt-4o").
            api_key (`SecretStr`, *optional*):
                The API key for the provider.
            **kwargs:
                Additional arguments for the provider.

        Returns:
            `InferenceProvider`: An instantiated provider.
        r"""
        from xrtm.forecast.core.config.inference import ProviderConfig
        from xrtm.forecast.core.config.main import settings

        request_kwargs = dict(kwargs)
        env_profile = request_kwargs.pop("env", None)
        config, provider_type, model_id = coerce_provider_request(config, provider_type, model_id)

        if config is None:
            config, provider_kwargs = build_config(provider_type=provider_type, model_id=model_id, api_key=api_key, kwargs=request_kwargs)
        elif isinstance(config, ProviderConfig):
            config, provider_kwargs = update_config(config=config, model_id=model_id, api_key=api_key, kwargs=request_kwargs)
        else:
            provider_kwargs = request_kwargs

        if env_profile:
            logger.info(f"Applying Environment Profile: {env_profile}")
        config = apply_environment_profile(config, env_profile)
        config = inject_api_key_from_settings(config, settings)
        return instantiate_provider(config, provider_kwargs)


__all__ = ["ModelFactory"]
