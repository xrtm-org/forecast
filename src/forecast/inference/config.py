from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, SecretStr


class ProviderConfig(BaseModel):
    """Base configuration for any inference provider."""

    model_id: str
    api_key: Optional[SecretStr] = None
    rpm: int = 15
    timeout: int = 30
    extra: Dict[str, Any] = Field(default_factory=dict)


class GeminiConfig(ProviderConfig):
    """Specific configuration for Google Gemini."""

    use_cheap_models: bool = True
    flash_model_id: str = "gemini-2.0-flash-lite"
    smart_model_id: str = "gemini-2.0-flash"
    redis_url: Optional[str] = "redis://localhost:6379"


class OpenAIConfig(ProviderConfig):
    """Specific configuration for OpenAI or compatible backends."""

    base_url: str = "https://api.openai.com/v1"
