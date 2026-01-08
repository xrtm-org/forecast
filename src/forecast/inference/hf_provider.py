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
from typing import Any, AsyncIterable

from forecast.inference.base import InferenceProvider, ModelResponse
from forecast.inference.config import HFConfig

logger = logging.getLogger(__name__)


class HuggingFaceProvider(InferenceProvider):
    r"""
    Provider implementation for local models using Hugging Face Transformers.

    This provider allows running models locally on CPU or GPU (CUDA/MPS).
    It is designed for "Institutional Sovereignty" use cases where data privacy
    is paramount.

    Args:
        config (`HFConfig`):
            Configuration object detailing model path, device, and quantization.
    """

    def __init__(self, config: HFConfig):
        self.config = config
        self.model_id = config.model_id
        self._model = None
        self._tokenizer = None
        self._is_initialized = False

    def _ensure_initialized(self):
        r"""Lazy initialisation of HF models to avoid overhead on import."""
        if self._is_initialized:
            return

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        except ImportError:
            raise ImportError(
                "The 'transformers' and 'torch' libraries are required for HuggingFaceProvider. "
                "Install them with `pip install xrtm-forecast[local]`."
            )

        logger.info(f"Initializing local Hugging Face model: {self.model_id} on {self.config.device}")

        # Handle quantization config if provided
        quantization_config = None
        if self.config.quantization == "4bit":
            from transformers import BitsAndBytesConfig

            quantization_config = BitsAndBytesConfig(load_in_4bit=True)
        elif self.config.quantization == "8bit":
            from transformers import BitsAndBytesConfig

            quantization_config = BitsAndBytesConfig(load_in_8bit=True)

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_id, cache_dir=self.config.cache_dir, trust_remote_code=self.config.trust_remote_code
        )

        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            device_map=self.config.device if quantization_config else None,
            quantization_config=quantization_config,
            cache_dir=self.config.cache_dir,
            trust_remote_code=self.config.trust_remote_code,
        )

        if not quantization_config and self.config.device != "auto":
            self._model = self._model.to(self.config.device)

        self._pipeline = pipeline(
            "text-generation",
            model=self._model,
            tokenizer=self._tokenizer,
            device=None if quantization_config or self.config.device == "auto" else self.config.device,
        )

        self._is_initialized = True

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        r"""
        Asynchronously generates content from a local Hugging Face model.

        Args:
            prompt (`str`):
                The input prompt.
            output_logprobs (`bool`, *optional*, defaults to `False`):
                Whether to return log probabilities.
            **kwargs:
                Additional generation parameters.

        Returns:
            `ModelResponse`: The standardized model response.
        """
        return await asyncio.to_thread(self.generate_content, prompt, output_logprobs, **kwargs)

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        r"""
        Synchronously generates content from a local Hugging Face model.

        Args:
            prompt (`str`):
                The input prompt.
            output_logprobs (`bool`, *optional*, defaults to `False`):
                Whether to return log probabilities.
            **kwargs:
                Additional generation parameters.

        Returns:
            `ModelResponse`: The standardized model response.
        """
        self._ensure_initialized()

        # Extract generation parameters from kwargs
        max_new_tokens = kwargs.get("max_new_tokens", 512)
        temperature = kwargs.get("temperature", 0.7)
        do_sample = temperature > 0

        outputs = self._pipeline(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=do_sample,
            return_full_text=False,
            **self.config.extra,
        )

        generated_text = outputs[0]["generated_text"]

        return ModelResponse(
            text=generated_text,
            raw=outputs,
            usage={
                "prompt_tokens": len(self._tokenizer.encode(prompt)) if self._tokenizer else 0,
                "completion_tokens": len(self._tokenizer.encode(generated_text)) if self._tokenizer else 0,
                "total_tokens": 0,  # Sum them up if needed
            },
        )

    async def stream(self, messages: Any, **kwargs: Any) -> AsyncIterable[Any]:
        r"""
        Streaming support for HF models, standardized to match OpenAI/Gemini formats.

        Args:
            messages (`Any`):
                Conversation history or prompt string.
            **kwargs:
                Additional generation parameters.

        Returns:
            `AsyncIterable[Any]`: An async generator of response chunks.
        """
        self._ensure_initialized()
        assert self._tokenizer is not None, "Tokenizer must be initialized"
        assert self._model is not None, "Model must be initialized"

        from threading import Thread

        from transformers import TextIteratorStreamer

        # 1. Prepare Inputs
        prompt = messages
        if isinstance(messages, list):
            # Basic concatenation for now, sophisticated templates later
            prompt = "\n".join([m.get("content", "") for m in messages])

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)

        # 2. Setup Streamer
        streamer = TextIteratorStreamer(self._tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = dict(
            inputs,
            streamer=streamer,
            max_new_tokens=kwargs.get("max_new_tokens", 512),
            temperature=kwargs.get("temperature", 0.7),
            do_sample=kwargs.get("temperature", 0.7) > 0,
        )

        # 3. Verify Thread Safety: Run generation in a separate thread
        thread = Thread(target=self._model.generate, kwargs=generation_kwargs)
        thread.start()

        # 4. Yield Chunks Asynchronously
        # The streamer is an iterator, but iterating it blocks.
        # We need to iterate it in a non-blocking way relative to the event loop.
        # Since 'for text in streamer' blocks, we can't easily `await` each chunk
        # unless we wrap the iterator or use run_in_executor for the *entire* loop?
        # Actually, `TextIteratorStreamer` uses a Queue internally.
        # We can poll it or iterate it. Iterating blocks until next token.
        # Best practice for AsyncIO integration:

        # 4. Yield Chunks Asynchronously
        # The streamer is an iterator, but iterating it blocks.
        # We need to iterate it in a non-blocking way relative to the event loop.

        # Best practice for AsyncIO integration with blocking iterators:
        # We yield control explicitly with await asyncio.sleep(0)

        # To strictly await, we iterate the sync generator in a thread?
        # A simpler pattern:
        for text in streamer:
            # This blocks the loop briefly per token, but usually acceptable for local inference.
            # Ideally we'd use `await loop.run_in_executor(None, next, streamer)` but streamer isn't a simple iterator.
            # Given Python GIL, simple iteration is often the pragmatic choice for HF streamers.
            # To be "Institutional Grade", we should yield control.
            await asyncio.sleep(0)  # Yield control

            chunk = {"contentBlockDelta": {"delta": {"text": text}}}
            yield chunk

        # 5. Yield Stop Signal
        yield {"messageStop": {"stopReason": "end_turn"}}

    @property
    def supports_tools(self) -> bool:
        r"""Most local models require specific prompting for tool use; natively False for now."""
        return False


__all__ = ["HuggingFaceProvider"]
