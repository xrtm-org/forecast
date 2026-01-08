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
    def get_provider(config: Optional[ProviderConfig] = None, tier: str = "SMART") -> InferenceProvider:
        r"""
        Creates and returns a provider instance based on the provided configuration.

        If no configuration is provided, it falls back to the global `forecast.config.settings`.

        Args:
            config (`ProviderConfig`, *optional*):
                The configuration object. If `None`, defaults are loaded from environment.
            tier (`str`, *optional*, defaults to `"SMART"`):
                The performance tier for the model.

        Returns:
            `InferenceProvider`: An instantiated and configured provider.

        Raises:
            `ValueError`: If the provided config type is not supported or no API keys are found.
        """
        from forecast.config import settings
        from forecast.exceptions import ConfigurationError

        if config is None:
            provider_type = settings.primary_provider
            if provider_type == "GEMINI":
                if not settings.gemini_api_key:
                    raise ConfigurationError("GEMINI_API_KEY not found in environment or settings.")
                config = GeminiConfig(
                    api_key=settings.gemini_api_key,
                    smart_model_id=settings.gemini_smart_model,
                    flash_model_id=settings.gemini_flash_model,
                )
            elif provider_type == "OPENAI":
                if not settings.openai_api_key:
                    raise ConfigurationError("OPENAI_API_KEY not found in environment or settings.")
                config = OpenAIConfig(
                    api_key=settings.openai_api_key,
                    model_id=settings.openai_model,
                    base_url=settings.openai_base_url,
                )

        if isinstance(config, GeminiConfig):
            from forecast.inference.gemini_provider import GeminiProvider

            return GeminiProvider(config=config, tier=tier)

        elif isinstance(config, OpenAIConfig):
            from forecast.inference.openai_provider import OpenAIProvider

            return OpenAIProvider(config=config)

        else:
            raise ConfigurationError(f"Unsupported configuration type or no config provided: {type(config)}")


__all__ = ["ModelFactory"]
