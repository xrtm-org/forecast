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

import logging
from typing import Any, AsyncIterable, Dict, List, Optional, cast

from openai import AsyncOpenAI, OpenAI

from forecast.inference.base import InferenceProvider, ModelResponse
from forecast.inference.config import OpenAIConfig

logger = logging.getLogger(__name__)


class OpenAIProvider(InferenceProvider):
    r"""
    Adapter for OpenAI and OpenAI-compatible APIs (e.g., Anthropic via proxy).

    This provider implements the `InferenceProvider` interface for the OpenAI
    Chat Completions API.

    Args:
        config (`OpenAIConfig`):
            Configuration object containing the API key, model ID, and optional base URL.
    """

    def __init__(self, config: OpenAIConfig, **kwargs: Any):
        r"""
        Initializes the OpenAI provider.

        Args:
            config (`OpenAIConfig`): Explicit OpenAI configuration.
            **kwargs: Additional provider-specific options.
        """
        self.config = config
        self.model_id = config.model_id
        self.api_key = config.api_key.get_secret_value() if config.api_key else None
        self.base_url = config.base_url

        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        self.sync_client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _normalize_messages(self, messages: Any) -> List[Dict[str, str]]:
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]
        return messages

    async def generate_content_async(
        self,
        prompt: Any,
        output_logprobs: bool = False,
        tools: Optional[List[Any]] = None,
        max_tool_turns: int = 5,
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
            **kwargs:
                Additional generation parameters.

        Returns:
            `ModelResponse`: The standardized model response.
        """
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

        current_turn = 0
        while current_turn < max_tool_turns:
            current_turn += 1
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                tools=cast(Any, openai_tools),
                logprobs=output_logprobs,
                top_logprobs=5 if output_logprobs else None,
                **kwargs,
            )

            choice = response.choices[0]
            if choice.message.tool_calls:
                logger.info(f"[OPENAI] Detected {len(choice.message.tool_calls)} tool calls. Turn {current_turn}")
                messages.append(choice.message)
                tool_outputs = await self._execute_tool_calls(choice.message.tool_calls, tools or [])
                messages.extend(tool_outputs)
                continue  # Handle the tool outputs in the next turn

            text = choice.message.content or ""
            normalized_logprobs = None
            if output_logprobs and choice.logprobs and choice.logprobs.content:
                normalized_logprobs = []
                for lp in choice.logprobs.content:
                    normalized_logprobs.append(
                        {
                            "token": lp.token,
                            "logprob": lp.logprob,
                        }
                    )

            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return ModelResponse(text=text, raw=response, usage=usage, logprobs=normalized_logprobs)

        from forecast.exceptions import ProviderError

        raise ProviderError(f"OpenAI generation failed: Max tool turns ({max_tool_turns}) exceeded.")

    async def _execute_tool_calls(self, tool_calls: List[Any], tools: List[Any]) -> List[Dict[str, Any]]:
        """Executes tool calls and returns OpenAI-formatted tool results."""
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
        self, prompt: Any, output_logprobs: bool = False, tools: Optional[List[Any]] = None, **kwargs: Any
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
            **kwargs:
                Additional generation parameters.

        Returns:
            `ModelResponse`: The standardized model response.
        """
        messages = self._normalize_messages(prompt or kwargs.get("messages"))

        response = self.sync_client.chat.completions.create(
            model=self.model_id,
            messages=cast(Any, messages),
            **kwargs,
        )

        choice = response.choices[0]
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return ModelResponse(text=choice.message.content or "", raw=response, usage=usage)

    async def _stream_generator(self, messages: Any, **kwargs) -> AsyncIterable[Any]:
        """Streaming implementation."""
        messages = self._normalize_messages(messages)
        stream = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            stream=True,
            **kwargs,
        )

        if hasattr(stream, "__aiter__"):
            async for chunk in cast(AsyncIterable[Any], stream):
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {"contentBlockDelta": {"delta": {"text": chunk.choices[0].delta.content}}}

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
        """
        return self._stream_generator(messages, **kwargs)


__all__ = ["OpenAIProvider"]
