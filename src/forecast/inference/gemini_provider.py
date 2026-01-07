import asyncio
import inspect
import logging
import time
from typing import Any, AsyncIterable, Dict, List, Optional, cast

from google import genai
from google.genai import types

from forecast.inference.base import InferenceProvider, ModelResponse
from forecast.inference.config import GeminiConfig
from forecast.telemetry.token_stream import TokenStreamContext
from forecast.utils.rate_limiter import TokenBucket

logger = logging.getLogger(__name__)


class GeminiProvider(InferenceProvider):
    """
    Native implementation for Google Gemini.
    Decoupled from application-level settings.
    """

    def __init__(self, config: GeminiConfig, tier: str = "SMART"):
        """
        Args:
            config: Explicit Gemini configuration.
            tier: Performance tier (SMART or FAST).
        """
        self.config = config
        self.model_id = config.model_id

        if not self.model_id:
            # Tiered Logic from config
            if config.use_cheap_models:
                if tier == "FAST":
                    self.model_id = config.flash_model_id
                else:
                    self.model_id = config.smart_model_id
            else:
                self.model_id = config.model_id or "gemini-2.0-flash"

        # Strip prefixes if any
        if "/" in self.model_id:
            self.model_id = self.model_id.split("/")[-1]

        key = config.api_key.get_secret_value() if config.api_key else None
        self.client = genai.Client(api_key=key)

        self.rate_limiter = None
        if "gemini" in self.model_id.lower() and "flash" in self.model_id.lower() and config.redis_url:
            self.rate_limiter = TokenBucket(
                redis_url=config.redis_url,
                key="gemini_flash_rate_limit",
                rate=config.rpm / 60.0,
                capacity=max(10, config.rpm // 3),
            )

    def mask_prompt(self, prompt: str) -> str:
        """Removes dates and sensitive patterns to prevent bias."""
        import re

        masked = re.sub(r"202[0-5]", "YEAR_X", prompt)
        return masked

    async def generate_content_async(
        self,
        prompt: Any,
        output_logprobs: bool = False,
        mask: bool = False,
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        import random

        if not self.supports_tools and tools:
            logger.warning(f"[Gemini] Model {self.model_id} does not support tools. Stripping tools.")
            tools = None

        max_retries = 3
        base_delay = 5
        max_tool_turns = 10

        messages = prompt or kwargs.get("messages")
        if not messages:
            logger.error("[GEMINI] generate_content_async called without prompt/messages")
            return ModelResponse(text="Error: No prompt provided", raw={})

        if mask and isinstance(messages, str):
            messages = self.mask_prompt(messages)

        contents, system_instruction = self._normalize_messages(messages)
        processed_tools = self._process_tools(tools)
        gemini_tools = [types.Tool(function_declarations=processed_tools)] if processed_tools else None

        response_logprobs = True if output_logprobs else None
        logprobs = 5 if output_logprobs else None

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=cast(Any, gemini_tools),
            response_logprobs=response_logprobs,
            logprobs=logprobs,
        )

        current_turn = 0
        while current_turn < max_tool_turns:
            current_turn += 1
            for i in range(max_retries):
                try:
                    if self.rate_limiter:
                        await self.rate_limiter.acquire()

                    response = await self.client.aio.models.generate_content(
                        model=self.model_id,
                        contents=cast(Any, contents),
                        config=cast(Any, config),
                    )

                    tool_calls = []
                    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if part.function_call:
                                tool_calls.append(part.function_call)

                    if tool_calls:
                        logger.info(f"[Gemini] Detected {len(tool_calls)} tool calls. Executing...")
                        if response.candidates and response.candidates[0].content:
                            contents.append(response.candidates[0].content)
                        tool_outputs = await self._execute_tool_calls(tool_calls, tools or [])
                        contents.append(types.Content(role="user", parts=tool_outputs))
                        continue

                    usage = {
                        "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                        "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                        "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                    }

                    response_text = ""
                    try:
                        response_text = response.text or ""
                    except Exception:
                        pass

                    TokenStreamContext().log(
                        prompt=str(prompt),
                        response=response_text,
                        model_id=self.model_id,
                        token_usage=usage,
                        latency_ms=0.0,
                        component_id="forecast_gemini_async",
                    )

                    token_logprobs: List[Dict[str, Any]] = []
                    if output_logprobs and response.candidates and response.candidates[0].logprobs_result:
                        try:
                            chosen = response.candidates[0].logprobs_result.chosen_candidates
                            if chosen is not None:
                                for candidate in chosen:
                                    if candidate.token is not None and candidate.log_probability is not None:
                                        token_logprobs.append(
                                            {"token": candidate.token, "logprob": float(candidate.log_probability)}
                                        )
                        except Exception as exc:
                            logger.warning(f"[Gemini] Logprob extraction failure: {exc}")

                    return ModelResponse(
                        text=response_text,
                        raw=response,
                        usage=usage,
                        logprobs=token_logprobs if token_logprobs else None,
                    )

                except Exception as e:
                    if "429" in str(e) and i < max_retries - 1:
                        delay = (base_delay * (2**i)) + (random.random() * 2)
                        logger.warning(f"Gemini 429 Detected (Async). Retrying in {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue
                    raise e
        return ModelResponse(text="Error: Max tool turns exceeded.", raw={})

    async def _execute_tool_calls(self, tool_calls: List[Any], tools: List[Any]) -> List[types.Part]:
        results = []
        # Create a map of tools by their cleaned names (Gemini restricted)
        name_map = {}
        import re

        for t in tools:
            # Protocol check: if it's a Tool instance, use its metadata
            if hasattr(t, "name") and hasattr(t, "run"):
                name = t.name
                func = t.run
            else:
                # Legacy / raw function fallback
                func = getattr(t, "fn", getattr(t, "_tool_func", t))
                name = getattr(func, "__name__", None) or getattr(t, "name", f"tool_{abs(hash(func))}")

            clean_name = re.sub(r"[^a-zA-Z0-9_\-.:]", "_", str(name))
            if not re.match(r"^[a-zA-Z_]", clean_name):
                clean_name = "f_" + clean_name
            clean_name = clean_name[:63]
            name_map[clean_name] = func

        for call in tool_calls:
            fname = call.name
            args = call.args
            if fname in name_map:
                try:
                    target = name_map[fname]
                    if asyncio.iscoroutinefunction(target):
                        res = await target(**args)
                    elif inspect.iscoroutinefunction(target): # Check for __call__ or tool.run
                        res = await target(**args)
                    else:
                        res = await asyncio.to_thread(target, **args)
                    content = str(res)
                except Exception as e:
                    logger.error(f"[Gemini] Tool Execution Failed for {fname}: {e}")
                    content = f"Error executing {fname}: {str(e)}"
            else:
                content = f"Error: Tool {fname} not found."
            results.append(types.Part.from_function_response(name=fname, response={"result": content}))
        return results

    def _execute_tool_calls_sync(self, tool_calls: List[Any], tools: List[Any]) -> List[types.Part]:
        results = []
        name_map = {}
        import re

        for t in tools:
            # Protocol check
            if hasattr(t, "name") and hasattr(t, "run"):
                name = t.name
                func = t.run
            else:
                func = getattr(t, "fn", getattr(t, "_tool_func", t))
                name = getattr(func, "__name__", None) or getattr(t, "name", f"tool_{abs(hash(func))}")

            clean_name = re.sub(r"[^a-zA-Z0-9_\-.:]", "_", str(name))
            if not re.match(r"^[a-zA-Z_]", clean_name):
                clean_name = "f_" + clean_name
            clean_name = clean_name[:63]
            name_map[clean_name] = func

        for call in tool_calls:
            fname = call.name
            args = call.args
            if fname in name_map:
                try:
                    target = name_map[fname]
                    if asyncio.iscoroutinefunction(target) or inspect.iscoroutinefunction(target):
                        content = f"Error: Cannot execute async tool {fname} in sync context."
                    else:
                        res = target(**args)
                        content = str(res)
                except Exception as e:
                    logger.error(f"[Gemini] Tool Execution Failed for {fname}: {e}")
                    content = f"Error executing {fname}: {str(e)}"
            else:
                content = f"Error: Tool {fname} not found."
            results.append(types.Part.from_function_response(name=fname, response={"result": content}))
        return results

    def generate_content(
        self,
        prompt: Any,
        output_logprobs: bool = False,
        mask: bool = False,
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        import random

        if not self.supports_tools and tools:
            logger.warning(f"[Gemini] Model {self.model_id} does not support tools. Stripping tools.")
            tools = None

        max_retries = 3
        base_delay = 5
        max_tool_turns = 10

        if mask and isinstance(prompt, str):
            prompt = self.mask_prompt(prompt)

        contents, system_instruction = self._normalize_messages(prompt)
        processed_tools = self._process_tools(tools)
        gemini_tools = [types.Tool(function_declarations=processed_tools)] if processed_tools else None

        response_logprobs = True if output_logprobs else None
        logprobs = 5 if output_logprobs else None

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=cast(Any, gemini_tools),
            response_logprobs=response_logprobs,
            logprobs=logprobs,
        )

        current_turn = 0
        while current_turn < max_tool_turns:
            current_turn += 1
            for i in range(max_retries):
                try:
                    if self.rate_limiter:
                        self.rate_limiter.acquire_sync()

                    response = self.client.models.generate_content(
                        model=self.model_id,
                        contents=cast(Any, contents),
                        config=cast(Any, config),
                    )

                    tool_calls = []
                    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if part.function_call:
                                tool_calls.append(part.function_call)

                    if tool_calls:
                        if response.candidates and response.candidates[0].content:
                            contents.append(response.candidates[0].content)
                        tool_outputs = self._execute_tool_calls_sync(tool_calls, tools or [])
                        contents.append(types.Content(role="user", parts=tool_outputs))
                        continue

                    usage = {
                        "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                        "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                        "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                    }

                    response_text = ""
                    try:
                        response_text = response.text or ""
                    except Exception:
                        pass

                    TokenStreamContext().log(
                        prompt=str(prompt),
                        response=response_text,
                        model_id=self.model_id,
                        token_usage=usage,
                        latency_ms=0.0,
                        component_id="forecast_gemini_sync",
                    )

                    token_logprobs: List[Dict[str, Any]] = []
                    if output_logprobs and response.candidates and response.candidates[0].logprobs_result:
                        try:
                            chosen = response.candidates[0].logprobs_result.chosen_candidates
                            if chosen:
                                for candidate in chosen:
                                    if candidate.token is not None and candidate.log_probability is not None:
                                        token_logprobs.append(
                                            {"token": candidate.token, "logprob": float(candidate.log_probability)}
                                        )
                        except Exception as exc:
                            logger.warning(f"[Gemini] Logprob extraction failure: {exc}")

                    return ModelResponse(
                        text=response_text,
                        raw=response,
                        usage=usage,
                        logprobs=token_logprobs if token_logprobs else None,
                    )
                except Exception as e:
                    if "429" in str(e) and i < max_retries - 1:
                        delay = (base_delay * (2**i)) + (random.random() * 2)
                        time.sleep(delay)
                        continue
                    raise e
        return ModelResponse(text="Error: Max tool turns exceeded.", raw={})

    def _process_tools(self, tools: Optional[List[Any]]) -> List[Any]:
        if not tools:
            return []
        import re

        processed = []

        def make_wrapper(func, n):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = n
            wrapper.__doc__ = getattr(func, "__doc__", "")
            return wrapper

        for t in tools:
            # Protocol check for Tool instances
            if hasattr(t, "parameters_schema") and hasattr(t, "run"):
                import copy
                spec = {
                    "name": t.name,
                    "description": t.description,
                    "parameters": copy.deepcopy(t.parameters_schema)
                }
                # Sanitize name
                spec["name"] = re.sub(r"[^a-zA-Z0-9_\-.:]", "_", spec["name"])
                if not re.match(r"^[a-zA-Z_]", spec["name"]):
                    spec["name"] = "f_" + spec["name"]
                spec["name"] = spec["name"][:63]
                processed.append(spec)
                continue

            if hasattr(t, "tool_spec") and isinstance(t.tool_spec, dict):
                import copy
                spec = copy.deepcopy(t.tool_spec)
                if "inputSchema" in spec and isinstance(spec["inputSchema"], dict):
                    if "json" in spec["inputSchema"]:
                        spec["inputSchema"] = spec["inputSchema"]["json"]
                    spec["parameters"] = spec.pop("inputSchema")
                if "parameters" in spec and isinstance(spec["parameters"], dict):
                    if "json" in spec["parameters"]:
                        spec["parameters"] = spec["parameters"]["json"]
                processed.append(spec)
                continue

            f = getattr(t, "fn", getattr(t, "_tool_func", t))
            raw_name = getattr(f, "__name__", None)
            if not raw_name or "<" in raw_name or "(" in raw_name:
                raw_name = getattr(t, "name", f"tool_{abs(hash(f))}")
            clean_name = re.sub(r"[^a-zA-Z0-9_\-.:]", "_", str(raw_name))
            if not re.match(r"^[a-zA-Z_]", clean_name):
                clean_name = "f_" + clean_name
            clean_name = clean_name[:63]
            if clean_name != getattr(f, "__name__", None):
                processed.append(make_wrapper(f, clean_name))
            else:
                processed.append(f)
        return processed

    def _normalize_messages(self, messages: Any) -> tuple[List[types.Content], Optional[str]]:
        if isinstance(messages, str):
            sentences = [{"role": "user", "content": messages}]
        elif isinstance(messages, list):
            sentences = messages
        else:
            sentences = [messages]
        contents = []
        system_instruction = None
        for msg in sentences:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                role = getattr(msg, "role", "user")
                content = getattr(msg, "content", "")
            if role in ["system", "developer"]:
                if isinstance(content, str):
                    system_instruction = content
                continue
            gemini_role = "user" if role == "user" else "model"
            parts = []
            if isinstance(content, str):
                parts.append(types.Part.from_text(text=content))
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, str):
                        parts.append(types.Part.from_text(text=part))
                    elif isinstance(part, dict) and "text" in part:
                        parts.append(types.Part.from_text(text=part["text"]))
                    elif hasattr(part, "text"):
                        parts.append(types.Part.from_text(text=part.text))
            if parts:
                contents.append(types.Content(role=gemini_role, parts=parts))
        return contents, system_instruction

    async def _stream_generator(self, *args, **kwargs) -> AsyncIterable[Any]:
        messages = kwargs.get("messages")
        if not messages:
            if len(args) >= 2 and isinstance(args[1], list):
                messages = args[1]
            elif args:
                messages = args[0]
        tools = kwargs.get("tools")
        processed_tools = self._process_tools(tools)
        if not messages:
            return
        contents, system_instruction = self._normalize_messages(messages)
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        final_system = system_instruction or kwargs.get("system_prompt")
        gemini_tools = [types.Tool(function_declarations=processed_tools)] if processed_tools else None
        config = types.GenerateContentConfig(system_instruction=final_system, tools=cast(Any, gemini_tools))

        def get_stream():
            return self.client.models.generate_content_stream(model=self.model_id, contents=contents, config=config)

        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockStart": {"start": {"type": "text"}, "contentBlockIndex": 0}}
        for chunk in await asyncio.to_thread(get_stream):
            try:
                chunk_text = chunk.text
                if chunk_text:
                    yield {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": chunk_text}}}
            except Exception:
                pass
            if hasattr(chunk, "candidates") and chunk.candidates:
                parts = chunk.candidates[0].content.parts
                for part in parts:
                    if hasattr(part, "function_call") and part.function_call:
                        yield {"messageDelta": {"delta": {"role": "assistant", "tool_calls": [part.function_call]}}}
        yield {"contentBlockStop": {"contentBlockIndex": 0}}
        yield {"messageStop": {"stopReason": "end_turn"}}

    def stream(self, *args, **kwargs) -> AsyncIterable[Any]:
        return self._stream_generator(*args, **kwargs)
