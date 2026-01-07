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
    def get_provider(config: ProviderConfig, tier: str = "SMART") -> InferenceProvider:
        r"""
        Creates and returns a provider instance based on the provided configuration.

        Args:
            config (`ProviderConfig`):
                The configuration object containing API keys and model settings.
            tier (`str`, *optional*, defaults to `"SMART"`):
                The performance tier for the model (specific to providers like Gemini).

        Returns:
            `InferenceProvider`: An instantiated and configured provider.

        Raises:
            `ValueError`: If the provided config type is not supported.

        Example:
            ```python
            >>> from forecast.inference.factory import ModelFactory
            >>> from forecast.inference.config import GeminiConfig
            >>> config = GeminiConfig(api_key="...", model_id="gemini-1.5-pro")
            >>> provider = ModelFactory.get_provider(config)
            ```
        """
        if isinstance(config, GeminiConfig):
            from forecast.inference.gemini_provider import GeminiProvider

            return GeminiProvider(config=config, tier=tier)

        elif isinstance(config, OpenAIConfig):
            from forecast.inference.openai_provider import OpenAIProvider

            return OpenAIProvider(config=config)

        else:
            raise ValueError(f"Unsupported configuration type: {type(config)}")


__all__ = ["ModelFactory"]
