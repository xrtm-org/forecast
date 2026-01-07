import logging
from typing import Any, AsyncIterable, Dict, List, Optional, cast

from openai import AsyncOpenAI, OpenAI

from forecast.inference.base import InferenceProvider, ModelResponse
from forecast.inference.config import OpenAIConfig

logger = logging.getLogger(__name__)


class OpenAIProvider(InferenceProvider):
    """
    Adapter for OpenAI and OAI-compatible APIs.
    Decoupled from application-level settings.
    """

    def __init__(self, config: OpenAIConfig):
        """
        Args:
            config: Explicit OpenAI configuration.
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
        **kwargs
    ) -> ModelResponse:
        """Standardized async generation."""
        # Cast to Any to satisfy strict mypy checks on the Union definition
        messages = cast(Any, self._normalize_messages(prompt or kwargs.get("messages")))

        openai_tools = None
        if tools:
            openai_tools = []
            for t in tools:
                if hasattr(t, "tool_spec"):
                    openai_tools.append({"type": "function", "function": t.tool_spec})
                else:
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": getattr(t, "__name__", str(t)),
                            "parameters": {"type": "object", "properties": {}}
                        }
                    })

        response = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            tools=cast(Any, openai_tools),
            logprobs=output_logprobs,
            top_logprobs=5 if output_logprobs else None,
            **kwargs
        )

        choice = response.choices[0]
        text = choice.message.content or ""

        normalized_logprobs = None
        if output_logprobs and choice.logprobs and choice.logprobs.content:
            normalized_logprobs = []
            for lp in choice.logprobs.content:
                normalized_logprobs.append({
                    "token": lp.token,
                    "logprob": lp.logprob,
                })

        if choice.message.tool_calls:
            logger.info(f"[OPENAI] Detected {len(choice.message.tool_calls)} tool calls.")

        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return ModelResponse(
            text=text,
            raw=response,
            usage=usage,
            logprobs=normalized_logprobs
        )

    def generate_content(
        self,
        prompt: Any,
        output_logprobs: bool = False,
        tools: Optional[List[Any]] = None,
        **kwargs
    ) -> ModelResponse:
        """Standardized sync generation."""
        messages = self._normalize_messages(prompt or kwargs.get("messages"))

        response = self.sync_client.chat.completions.create(
            model=self.model_id,
            messages=cast(Any, messages),
            logprobs=output_logprobs,
            **kwargs
        )

        choice = response.choices[0]
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return ModelResponse(
            text=choice.message.content or "",
            raw=response,
            usage=usage
        )

    async def _stream_generator(self, messages: Any, **kwargs) -> AsyncIterable[Any]:
        """Streaming implementation."""
        messages = self._normalize_messages(messages)
        stream = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            stream=True,
            **kwargs
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield {"contentBlockDelta": {"delta": {"text": chunk.choices[0].delta.content}}}

        yield {"messageStop": {"stopReason": "end_turn"}}

    def stream(self, messages: Any, **kwargs) -> AsyncIterable[Any]:
        """Streaming implementation wrapper."""
        return self._stream_generator(messages, **kwargs)
