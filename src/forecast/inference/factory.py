import logging

from forecast.inference.base import InferenceProvider
from forecast.inference.config import GeminiConfig, OpenAIConfig, ProviderConfig

logger = logging.getLogger(__name__)


class ModelFactory:
    """
    Central hub for instantiating model providers.
    Injected with configuration to ensure modularity.
    """

    @staticmethod
    def get_provider(config: ProviderConfig, tier: str = "SMART") -> InferenceProvider:
        """
        Returns an orchestrated provider instance.
        """
        if isinstance(config, GeminiConfig):
            from forecast.inference.gemini_provider import GeminiProvider

            return GeminiProvider(config=config, tier=tier)

        elif isinstance(config, OpenAIConfig):
            from forecast.inference.openai_provider import OpenAIProvider

            return OpenAIProvider(config=config)

        else:
            raise ValueError(f"Unsupported configuration type: {type(config)}")
