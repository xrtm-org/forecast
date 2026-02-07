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

import asyncio
import logging
import threading
from typing import Any, AsyncIterable, Dict, List

from xrtm.forecast.core.config.inference import LlamaCppConfig
from xrtm.forecast.providers.inference.base import InferenceProvider, ModelResponse

logger = logging.getLogger(__name__)


class LlamaCppProvider(InferenceProvider):
    r"""
    Provider implementation for CPU-optimized local inference via Llama-CPP-Python.
    Supports GGUF models. Requires 'llama-cpp' extra.
    r"""

    def __init__(self, config: LlamaCppConfig):
        self.config = config
        self.model_path = config.model_id  # Often a path to .gguf
        self._llm = None
        self._is_initialized = False
        self._init_lock = threading.Lock()

    def _ensure_initialized(self):
        if self._is_initialized:
            return

        with self._init_lock:
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
        return await asyncio.to_thread(self._generate_sync, prompt, **kwargs)

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        return self._generate_sync(prompt, **kwargs)

    def _generate_sync(self, prompt: str, **kwargs: Any) -> ModelResponse:
        self._ensure_initialized()
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

    async def _async_iter(self, sync_iterable: Any) -> AsyncIterable[Any]:
        """
        Helper to iterate over a synchronous generator in a thread
        to avoid blocking the main event loop.
        """
        iterator = iter(sync_iterable)

        def safe_next(it):
            try:
                return next(it), False
            except StopIteration:
                return None, True

        while True:
            chunk, is_done = await asyncio.to_thread(safe_next, iterator)
            if is_done:
                break
            yield chunk

    async def stream(self, messages: List[Dict[str, str]], **kwargs: Any) -> AsyncIterable[Any]:
        await asyncio.to_thread(self._ensure_initialized)
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

        async for chunk in self._async_iter(stream):
            text = chunk["choices"][0]["text"]
            yield {"contentBlockDelta": {"delta": {"text": text}}}

        yield {"messageStop": {"stopReason": "end_turn"}}

    @property
    def supports_tools(self) -> bool:
        return False


__all__ = ["LlamaCppProvider"]
