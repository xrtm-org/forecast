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

import logging
from typing import Optional

from pydantic import SecretStr

from forecast.inference.base import InferenceProvider
from forecast.inference.config import GeminiConfig, OpenAIConfig, ProviderConfig

logger = logging.getLogger(__name__)


class ModelFactory:
    r"""
    A centralized factory for instantiating various LLM inference providers.

    `ModelFactory` decouples the creation of providers from their specific
    implementations, using `ProviderConfig` objects to drive the instantiation logic.
    """

    @staticmethod
    def get_provider(
        config: Optional[ProviderConfig] = None,
        provider_type: Optional[str] = None,
        model_id: Optional[str] = None,
        api_key: Optional[SecretStr] = None,
        **kwargs,
    ) -> InferenceProvider:
        """
        Creates and returns a provider instance.

        Args:
            config (`ProviderConfig`, *optional*):
                The configuration object.
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
        """
        from forecast.exceptions import ConfigurationError

        if config is None:
            if not provider_type or not model_id or not api_key:
                raise ConfigurationError(
                    "Explicitly provide either a `config` object or `provider_type`, `model_id`, and `api_key`."
                )

            if provider_type.upper() == "GEMINI":
                config = GeminiConfig(model_id=model_id, api_key=api_key, **kwargs)
            elif provider_type.upper() == "OPENAI":
                config = OpenAIConfig(model_id=model_id, api_key=api_key, **kwargs)

        if isinstance(config, GeminiConfig):
            from forecast.inference.gemini_provider import GeminiProvider

            return GeminiProvider(config=config)

        elif isinstance(config, OpenAIConfig):
            from forecast.inference.openai_provider import OpenAIProvider

            return OpenAIProvider(config=config)

        else:
            raise ConfigurationError(f"Unsupported configuration type: {type(config)}")


__all__ = ["ModelFactory"]
