# coding=utf-8
# Copyright 2026 XRTM Team. All rights reserved.

import asyncio
import logging
from typing import Any, AsyncIterable, Dict, List

from forecast.core.config.inference import VLLMConfig
from forecast.providers.inference.base import InferenceProvider, ModelResponse

logger = logging.getLogger(__name__)


class VLLMProvider(InferenceProvider):
    """
    Provider implementation for high-throughput local inference via vLLM.
    Requires 'vllm' extra to be installed.
    """

    def __init__(self, config: VLLMConfig):
        self.config = config
        self.model_id = config.model_id
        self._engine = None
        self._is_initialized = False

    def _ensure_initialized(self):
        if self._is_initialized:
            return

        try:
            from vllm import LLM, SamplingParams
        except ImportError:
            raise ImportError(
                "The 'vllm' library is required for VLLMProvider. Install it with `pip install xrtm-forecast[vllm]`."
            )

        logger.info(f"Initializing vLLM engine: {self.model_id}")
        self._engine = LLM(
            model=self.model_id,
            tensor_parallel_size=self.config.tensor_parallel_size,
            gpu_memory_utilization=self.config.gpu_memory_utilization,
            max_model_len=self.config.max_model_len,
            **self.config.extra,
        )
        self._sampling_params_class = SamplingParams
        self._is_initialized = True

    async def generate_content_async(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        self._ensure_initialized()
        # vLLM is typically used with its own async engine for server use cases,
        # but for direct library use we can use the LLM class.
        # Note: vLLM.generate is synchronous.
        return await asyncio.to_thread(self._generate_sync, prompt, **kwargs)

    def generate_content(self, prompt: str, output_logprobs: bool = False, **kwargs: Any) -> ModelResponse:
        self._ensure_initialized()
        return self._generate_sync(prompt, **kwargs)

    def _generate_sync(self, prompt: str, **kwargs: Any) -> ModelResponse:
        if self._engine is None:
            raise RuntimeError("vLLM engine failed to initialize.")

        sampling_params = self._sampling_params_class(
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_new_tokens", 512),
            **kwargs.get("sampling_extra", {}),
        )
        outputs = self._engine.generate([prompt], sampling_params)
        output = outputs[0]

        return ModelResponse(
            text=output.outputs[0].text,
            raw=output,
            usage={
                "prompt_tokens": len(output.prompt_token_ids),
                "completion_tokens": len(output.outputs[0].token_ids),
                "total_tokens": len(output.prompt_token_ids) + len(output.outputs[0].token_ids),
            },
        )

    async def stream(self, messages: List[Dict[str, str]], **kwargs: Any) -> AsyncIterable[Any]:
        # Placeholder for VLLM streaming
        if False:
            yield {}
        raise NotImplementedError("Streaming for VLLMProvider is not yet implemented via direct LLM class.")

    @property
    def supports_tools(self) -> bool:
        return False


__all__ = ["VLLMProvider"]
