import logging
import os

from pydantic import SecretStr

from forecast.inference.config import GeminiConfig, OpenAIConfig


def get_example_config(provider: str = "gemini"):
    """
    Returns a standardized config for examples based on environment variables.
    Provides a central place to swap models for all example scripts.
    """
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "mock-key")
        return GeminiConfig(
            api_key=SecretStr(api_key),
            model_id=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        )
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "mock-key")
        return OpenAIConfig(
            api_key=SecretStr(api_key),
            model_id=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def setup_example_logging():
    """Sets up a clean logging format for examples."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s"
    )
