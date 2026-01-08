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
from typing import Any, AsyncIterable, Dict, List

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

    async def generate_content_async(
        self, prompt: str, output_logprobs: bool = False, **kwargs: Any
    ) -> ModelResponse:
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

    def stream(self, messages: List[Dict[str, str]], **kwargs: Any) -> AsyncIterable[Any]:
        r"""
        Streaming support for HF (limited implementation).

        Args:
            messages (`List[Dict[str, str]]`):
                Conversation history.
            **kwargs:
                Additional generation parameters.

        Returns:
            `AsyncIterable[Any]`: An async generator of response chunks.
        """
        raise NotImplementedError("Streaming is not yet implemented for HuggingFaceProvider.")

    @property
    def supports_tools(self) -> bool:
        r"""Most local models require specific prompting for tool use; natively False for now."""
        return False


__all__ = ["HuggingFaceProvider"]
