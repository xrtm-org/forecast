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

r"""OpenAI inference provider.

Concrete implementation of ``InferenceProvider`` for the OpenAI
API, supporting chat completions, streaming, function calling,
structured output with JSON mode, and reasoning-capable models
(``reasoning_content`` handling plus a ``thinking`` mode toggle).
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, AsyncIterable, Dict, Iterable, List, Optional, cast

from openai import AsyncOpenAI, OpenAI

from xrtm.forecast.core.cache import InferenceCache
from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.core.exceptions import EmptyContentError, ProviderError
from xrtm.forecast.providers.inference.base import InferenceProvider, ModelResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(InferenceProvider):
    r"""
    Adapter for OpenAI and OpenAI-compatible APIs (e.g., Anthropic via proxy).

    This provider implements the `InferenceProvider` interface for the OpenAI
    Chat Completions API.

    Args:
        config (`OpenAIConfig`):
            Configuration object containing the API key, model ID, and optional base URL.
    r"""

    def __init__(self, config: OpenAIConfig, **kwargs: Any):
        r"""
        Initializes the OpenAI provider.

        Args:
            config (`OpenAIConfig`): Explicit OpenAI configuration.
            **kwargs: Additional provider-specific options.
        r"""
        self.config = config
        self.model_id = config.model_id
        self.knowledge_cutoff = config.knowledge_cutoff
        self.api_key = config.api_key.get_secret_value() if config.api_key else None
        self.base_url = config.base_url
        self.cache: Optional[InferenceCache] = kwargs.pop("cache", None)
        # Enable default cache if none provided
        if self.cache is None:
            try:
                self.cache = InferenceCache()
            except Exception:
                pass  # cache is optional

        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=config.timeout)
        self.sync_client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=config.timeout)

    def _normalize_messages(self, messages: Any) -> List[Dict[str, str]]:
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]
        return messages

    def _build_request_kwargs(
        self,
        kwargs: Dict[str, Any],
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        r"""Merge generation kwargs with provider-level thinking and response-format options."""
        request_kwargs = dict(kwargs)
        if response_format is not None:
            request_kwargs["response_format"] = response_format
        if self.config.thinking in ("enabled", "disabled"):
            extra_body = dict(request_kwargs.get("extra_body") or {})
            extra_body.setdefault("thinking", {"type": self.config.thinking})
            request_kwargs["extra_body"] = extra_body
        return request_kwargs

    @staticmethod
    def _extract_usage(response: Any) -> Dict[str, int]:
        r"""Normalize token usage, including cached prompt and reasoning tokens.

        Handles the OpenAI ``prompt_tokens_details.cached_tokens`` shape and the
        DeepSeek ``prompt_cache_hit_tokens`` shape, plus reasoning-token fields.
        """
        usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        raw_usage = getattr(response, "usage", None)
        if not raw_usage:
            return usage

        usage["prompt_tokens"] = int(getattr(raw_usage, "prompt_tokens", 0) or 0)
        usage["completion_tokens"] = int(getattr(raw_usage, "completion_tokens", 0) or 0)
        usage["total_tokens"] = int(getattr(raw_usage, "total_tokens", 0) or 0)

        prompt_details = getattr(raw_usage, "prompt_tokens_details", None)
        cached = getattr(prompt_details, "cached_tokens", None) if prompt_details is not None else None
        if cached is None:
            cached = getattr(raw_usage, "prompt_cache_hit_tokens", None)
        if cached is not None:
            usage["cached_prompt_tokens"] = int(cached or 0)

        completion_details = getattr(raw_usage, "completion_tokens_details", None)
        reasoning = (
            getattr(completion_details, "reasoning_tokens", None) if completion_details is not None else None
        )
        if reasoning is None:
            reasoning = getattr(raw_usage, "reasoning_tokens", None)
        if reasoning is not None:
            usage["reasoning_tokens"] = int(reasoning or 0)

        return usage

    @staticmethod
    def _extract_message_payload(choice: Any) -> tuple[str, Dict[str, Any]]:
        r"""Return ``(text, metadata)`` for a choice, raising on empty content.

        Reasoning models may fill ``reasoning_content`` while leaving ``content``
        empty; that must never silently degrade into a parse-failure fallback.
        """
        text = choice.message.content or ""
        reasoning = getattr(choice.message, "reasoning_content", None)
        metadata: Dict[str, Any] = {}
        if reasoning:
            metadata["reasoning_content"] = reasoning
        if not text:
            finish_reason = getattr(choice, "finish_reason", None)
            raise EmptyContentError(
                "OpenAI-compatible provider returned empty content "
                f"(finish_reason={finish_reason!r}, reasoning_chars={len(reasoning or '')}). "
                "Reasoning models may have spent the output budget on reasoning_content: "
                "disable thinking mode or raise max_tokens."
            )
        return text, metadata

    async def generate_content_async(
        self,
        prompt: Any,
        output_logprobs: bool = False,
        tools: Optional[List[Any]] = None,
        max_tool_turns: int = 5,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        r"""
        Asynchronously generates content from OpenAI.

        Args:
            prompt (`Any`):
                The input prompt or list of messages.
            output_logprobs (`bool`, *optional*, defaults to `False`):
                Whether to return log probabilities.
            tools (`List[Any]`, *optional*):
                Optional list of tools for function calling.
            max_tool_turns (`int`, *optional*, defaults to `5`):
                Maximum number of tool-execution turns to prevent infinite loops.
            response_format (`Dict[str, Any]`, *optional*):
                OpenAI-compatible structured-output request (e.g. ``{"type": "json_object"}``).
            **kwargs:
                Additional generation parameters.

        Returns:
            `ModelResponse`: The standardized model response.

        Raises:
            EmptyContentError: When the provider returns no text content.
        r"""
        # Cast to Any to satisfy strict mypy checks on the Union definition
        messages = cast(Any, self._normalize_messages(prompt or kwargs.get("messages")))

        openai_tools = None
        if tools:
            openai_tools = []
            for t in tools:
                if hasattr(t, "tool_spec"):
                    openai_tools.append({"type": "function", "function": t.tool_spec})
                else:
                    openai_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": getattr(t, "__name__", str(t)),
                                "parameters": {"type": "object", "properties": {}},
                            },
                        }
                    )

        request_kwargs = self._build_request_kwargs(kwargs, response_format)

        cache_key = self._cache_key_for_request(messages, tools, output_logprobs, request_kwargs)
        if cache_key and self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return ModelResponse(text=cached, metadata={"cache_hit": True})

        current_turn = 0
        while current_turn < max_tool_turns:
            current_turn += 1

            # Retry loop for transient API errors (timeouts, rate limits)
            max_retries = self.config.max_retries
            backoff_base = self.config.backoff_base
            for attempt in range(max_retries + 1):
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model_id,
                        messages=messages,
                        tools=cast(Any, openai_tools),
                        logprobs=output_logprobs,
                        top_logprobs=5 if output_logprobs else None,
                        **request_kwargs,
                    )
                    break
                except Exception as exc:
                    if attempt < max_retries:
                        wait = backoff_base ** attempt
                        logger.warning(f"[OPENAI] API error, retry {attempt+1}/{max_retries} in {wait:.1f}s: {exc}")
                        await asyncio.sleep(wait)
                    else:
                        raise

            choice = response.choices[0]
            if choice.message.tool_calls:
                logger.info(f"[OPENAI] Detected {len(choice.message.tool_calls)} tool calls. Turn {current_turn}")
                messages.append(choice.message)
                tool_outputs = await self._execute_tool_calls(choice.message.tool_calls, tools or [])
                messages.extend(tool_outputs)
                continue

            text, metadata = self._extract_message_payload(choice)

            normalized_logprobs = None
            if output_logprobs and choice.logprobs and choice.logprobs.content:
                normalized_logprobs = []
                for lp in choice.logprobs.content:
                    normalized_logprobs.append({"token": lp.token, "logprob": lp.logprob})

            usage = self._extract_usage(response)

            if cache_key and self.cache:
                self.cache.set(cache_key, text, {"model": self.model_id})

            return ModelResponse(text=text, raw=response, usage=usage, logprobs=normalized_logprobs, metadata=metadata)

        raise ProviderError(f"OpenAI generation failed: Max tool turns ({max_tool_turns}) exceeded.")

    async def _execute_tool_calls(self, tool_calls: List[Any], tools: List[Any]) -> List[Dict[str, Any]]:
        r"""Executes tool calls and returns OpenAI-formatted tool results."""
        results = []
        import json

        for call in tool_calls:
            tool_name = call.function.name
            args = json.loads(call.function.arguments)

            # Find tool in the list
            target_tool = None
            for t in tools:
                if hasattr(t, "name") and t.name == tool_name:
                    target_tool = t
                    break
                if getattr(t, "__name__", None) == tool_name:
                    target_tool = t
                    break

            if target_tool:
                try:
                    if hasattr(target_tool, "execute"):
                        output = await target_tool.execute(**args)
                    elif hasattr(target_tool, "run"):
                        output = await target_tool.run(**args)
                    else:
                        output = target_tool(**args)
                    result_str = str(output)
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    result_str = f"Error: {e}"
            else:
                result_str = f"Error: Tool {tool_name} not found."

            results.append(
                {
                    "tool_call_id": call.id,
                    "role": "tool",
                    "name": tool_name,
                    "content": result_str,
                }
            )
        return results

    def generate_content(
        self,
        prompt: Any,
        output_logprobs: bool = False,
        tools: Optional[List[Any]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        r"""
        Synchronously generates content from OpenAI.

        Args:
            prompt (`Any`):
                The input prompt or list of messages.
            output_logprobs (`bool`, *optional*, defaults to `False`):
                Whether to return log probabilities.
            tools (`List[Any]`, *optional*):
                Optional list of tools for function calling.
            response_format (`Dict[str, Any]`, *optional*):
                OpenAI-compatible structured-output request.
            **kwargs:
                Additional generation parameters.

        Returns:
            `ModelResponse`: The standardized model response.

        Raises:
            EmptyContentError: When the provider returns no text content.
        r"""
        messages = self._normalize_messages(prompt or kwargs.get("messages"))
        request_kwargs = self._build_request_kwargs(kwargs, response_format)

        cache_key = self._cache_key_for_request(messages, tools, output_logprobs, request_kwargs)
        if cache_key and self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return ModelResponse(text=cached, metadata={"cache_hit": True})

        response = self.sync_client.chat.completions.create(
            model=self.model_id,
            messages=cast(Any, messages),
            **request_kwargs,
        )

        choice = response.choices[0]
        text, metadata = self._extract_message_payload(choice)
        usage = self._extract_usage(response)
        if cache_key and self.cache:
            self.cache.set(cache_key, text, {"model": self.model_id})

        return ModelResponse(text=text, raw=response, usage=usage, metadata=metadata)

    def _cache_key_for_request(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Any]],
        output_logprobs: bool,
        kwargs: Dict[str, Any],
    ) -> Optional[str]:
        if self.cache is None or tools or output_logprobs or kwargs.get("stream"):
            return None
        try:
            return self.cache.compute_chat_key(self.model_id, messages, **kwargs)
        except (TypeError, ValueError) as e:
            logger.debug(f"[OPENAI] Request is not cacheable: {e}")
            return None

    async def _iter_stream_chunks(self, stream: Any) -> AsyncGenerator[Any, None]:
        if hasattr(stream, "__aiter__"):
            async for chunk in cast(AsyncIterable[Any], stream):
                yield chunk
            return

        if hasattr(stream, "__iter__"):
            iterator = iter(cast(Iterable[Any], stream))

            def safe_next() -> tuple[Any, bool]:
                try:
                    return next(iterator), False
                except StopIteration:
                    return None, True

            try:
                while True:
                    chunk, is_done = await asyncio.to_thread(safe_next)
                    if is_done:
                        break
                    yield chunk
            finally:
                close = getattr(iterator, "close", None)
                if close is not None:
                    try:
                        close()
                    except RuntimeError as exc:
                        logger.debug(f"[OPENAI] Streaming iterator close deferred: {exc}")
            return

        raise ProviderError("OpenAI streaming response is not iterable.")

    async def _stream_generator(self, messages: Any, **kwargs) -> AsyncIterable[Any]:
        r"""Streaming implementation."""
        messages = self._normalize_messages(messages)
        stream = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            stream=True,
            **kwargs,
        )

        chunks = self._iter_stream_chunks(stream)
        completed = False
        try:
            async for chunk in chunks:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {"contentBlockDelta": {"delta": {"text": chunk.choices[0].delta.content}}}
            completed = True
        finally:
            await chunks.aclose()

        if completed:
            yield {"messageStop": {"stopReason": "end_turn"}}

    def stream(self, messages: Any, **kwargs: Any) -> AsyncIterable[Any]:
        r"""
        Opens a streaming connection to OpenAI.

        Args:
            messages (`Any`):
                Conversation history or prompt.
            **kwargs:
                Additional generation parameters.

        Returns:
            `AsyncIterable[Any]`: An async generator of response chunks.
        r"""
        return self._stream_generator(messages, **kwargs)


__all__ = ["OpenAIProvider"]
