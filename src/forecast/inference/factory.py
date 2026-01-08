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
from typing import Any, Optional

from pydantic import SecretStr

from forecast.inference.base import InferenceProvider
from forecast.inference.config import GeminiConfig, HFConfig, OpenAIConfig, XLMConfig

logger = logging.getLogger(__name__)


class ModelFactory:
    r"""
    A centralized factory for instantiating various LLM inference providers.

    `ModelFactory` decouples the creation of providers from their specific
    implementations, using `ProviderConfig` objects to drive the instantiation logic.
    """

    @staticmethod
    def get_provider(
        config: Optional[Any] = None,
        provider_type: Optional[str] = None,
        model_id: Optional[str] = None,
        api_key: Optional[SecretStr] = None,
        **kwargs,
    ) -> InferenceProvider:
        """
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
        """
        from forecast.exceptions import ConfigurationError

        # Ergonomic Shortcut: string input
        if isinstance(config, str):
            if ":" in config:
                provider_type, model_id = config.split(":", 1)
            else:
                provider_type = config
            config = None

        if config is None:
            if not provider_type:
                raise ConfigurationError(
                    "Explicitly provide either a `config` object or `provider_type` (or a shortcut string)."
                )

            if provider_type.upper() == "GEMINI":
                # model_id is allowed to be None here; the injection layer will handle defaults later?
                # Actually, GeminiConfig requires model_id. We'll set a smart default if missing.
                mid = model_id or "gemini-2.0-flash"
                config = GeminiConfig(model_id=mid, api_key=api_key, **kwargs)
            elif provider_type.upper() == "OPENAI":
                mid = model_id or "gpt-4o"
                config = OpenAIConfig(model_id=mid, api_key=api_key, **kwargs)
            elif provider_type.upper() in ["HF", "HUGGINGFACE"]:
                mid = model_id or "sshleifer/tiny-gpt2"  # Minimal default for testing
                config = HFConfig(model_id=mid, **kwargs)
            else:
                raise ConfigurationError(f"Unsupported provider type: {provider_type}")

        from forecast.config import settings

        # Handle Environment Profiles if requested
        env_profile = kwargs.get("env")
        if env_profile:
            logger.info(f"Applying Environment Profile: {env_profile}")
            if env_profile == "production" and isinstance(config, OpenAIConfig):
                config.model_id = "gpt-4o"  # Override for production
            elif env_profile == "dev":
                config.model_id = "gpt-4o-mini" if isinstance(config, OpenAIConfig) else "gemini-2.0-flash"

        # Injection Layer: Resolve API keys from global settings if missing in component config

        if isinstance(config, GeminiConfig):
            if not config.api_key and settings.gemini_api_key:
                config.api_key = settings.gemini_api_key

            from forecast.inference.gemini_provider import GeminiProvider

            return GeminiProvider(config=config, **kwargs)

        elif isinstance(config, OpenAIConfig):
            if not config.api_key and settings.openai_api_key:
                config.api_key = settings.openai_api_key

            from forecast.inference.openai_provider import OpenAIProvider

            return OpenAIProvider(config=config, **kwargs)

        elif isinstance(config, (HFConfig, XLMConfig)):
            from forecast.inference.hf_provider import HuggingFaceProvider

            return HuggingFaceProvider(config=config)

        else:
            raise ConfigurationError(f"Unsupported configuration type: {type(config)}")


__all__ = ["ModelFactory"]
