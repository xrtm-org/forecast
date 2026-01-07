from abc import ABC, abstractmethod
from typing import Any, AsyncIterable, Dict, List, Optional


class InferenceProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    Standardizes interaction across different SDKs (Gemini, OpenAI, Anthropic, etc.).
    """

    @abstractmethod
    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs) -> Any:
        """Standardized async generation."""
        pass

    @property
    def supports_tools(self) -> bool:
        """
        Feature flag: Does this provider support native tool/function calling?
        Defaults to True for modern providers. Override if False.
        """
        return True

    @abstractmethod
    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs) -> Any:
        """Standardized sync generation."""
        pass

    @abstractmethod
    def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterable[Any]:
        """Standardized streaming interface."""
        pass


class ModelResponse:
    """Standardized response wrapper to normalize field access across SDKs."""

    def __init__(
        self,
        text: str,
        raw: Any = None,
        usage: Optional[Dict[str, int]] = None,
        logprobs: Optional[List[Dict[str, Any]]] = None,
    ):
        self.text = text
        self.raw = raw
        self.usage = usage or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.logprobs = logprobs
