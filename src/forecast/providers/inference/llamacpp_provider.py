# coding=utf-8
# Copyright 2026 XRTM Team. All rights reserved.

import asyncio
import logging
from typing import Any, AsyncIterable, Dict, List

from forecast.core.config.inference import LlamaCppConfig
from forecast.providers.inference.base import InferenceProvider, ModelResponse

logger = logging.getLogger(__name__)


class LlamaCppProvider(InferenceProvider):
    """
    Provider implementation for CPU-optimized local inference via Llama-CPP-Python.
    Supports GGUF models. Requires 'llama-cpp' extra.
    """

    def __init__(self, config: LlamaCppConfig):
        self.config = config
        self.model_path = config.model_id  # Often a path to .gguf
        self._llm = None
        self._is_initialized = False

    def _ensure_initialized(self):
        if self._is_initialized:
            return

        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "The 'llama-cpp-python' library is required for LlamaCppProvider. "
                "Install it with `pip install xrtm-forecast[llama-cpp]`."
            )

        logger.info(f"Initializing Llama-CPP model: {self.model_path}")
        self._llm = Llama(
            model_path=self.model_path,
            n_ctx=self.config.n_ctx,
            n_threads=self.config.n_threads,
            n_gpu_layers=self.config.n_gpu_layers,
            **self.config.extra,
        )
        self._is_initialized = True

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        self._ensure_initialized()
        return await asyncio.to_thread(self._generate_sync, prompt, **kwargs)

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        self._ensure_initialized()
        return self._generate_sync(prompt, **kwargs)

    def _generate_sync(self, prompt: str, **kwargs: Any) -> ModelResponse:
        if self._llm is None:
            raise RuntimeError("Llama-CPP model failed to initialize.")

        response = self._llm(
            prompt,
            max_tokens=kwargs.get("max_new_tokens", 512),
            temperature=kwargs.get("temperature", 0.7),
            **kwargs.get("extra_generation_params", {}),
        )

        # response is a dict matching OpenAI chat completion format partially
        text = response["choices"][0]["text"]
        usage = response.get("usage", {})

        return ModelResponse(
            text=text,
            raw=response,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )

    async def stream(self, messages: List[Dict[str, str]], **kwargs: Any) -> AsyncIterable[Any]:
        self._ensure_initialized()
        if self._llm is None:
            raise RuntimeError("Llama-CPP model failed to initialize.")

        # Llama-CPP-Python support streaming
        prompt = str(messages)  # Simplified conversion for base provider

        stream = self._llm(
            prompt,
            max_tokens=kwargs.get("max_new_tokens", 512),
            temperature=kwargs.get("temperature", 0.7),
            stream=True,
        )

        for chunk in stream:
            text = chunk["choices"][0]["text"]
            yield {"contentBlockDelta": {"delta": {"text": text}}}
            await asyncio.sleep(0)

        yield {"messageStop": {"stopReason": "end_turn"}}

    @property
    def supports_tools(self) -> bool:
        return False


__all__ = ["LlamaCppProvider"]
