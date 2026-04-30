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
import queue
import sys
import threading
import time
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from xrtm.forecast.core.cache import InferenceCache
from xrtm.forecast.core.config.inference import HFConfig, LlamaCppConfig, OpenAIConfig, VLLMConfig
from xrtm.forecast.core.exceptions import ProviderError
from xrtm.forecast.providers.inference.hf_provider import HuggingFaceProvider
from xrtm.forecast.providers.inference.llamacpp_provider import LlamaCppProvider
from xrtm.forecast.providers.inference.openai_provider import OpenAIProvider
from xrtm.forecast.providers.inference.vllm_provider import VLLMProvider


class FakeOpenAICompletions:
    def __init__(self) -> None:
        self.call_count = 0

    def create(self, **_: Any) -> Any:
        self.call_count += 1
        message = SimpleNamespace(content=f"response-{self.call_count}", tool_calls=None)
        choice = SimpleNamespace(message=message)
        usage = SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2)
        return SimpleNamespace(choices=[choice], usage=usage)


def openai_stream_chunk(text: str) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


def test_openai_sync_cache_hits_only_for_cacheable_requests(tmp_path):
    cache = InferenceCache(db_path=str(tmp_path / "cache.db"))
    provider = OpenAIProvider(OpenAIConfig(model_id="gpt-test", api_key="fake"), cache=cache)
    completions = FakeOpenAICompletions()
    provider.sync_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))  # type: ignore[assignment]

    first = provider.generate_content("Hello", temperature=0)
    second = provider.generate_content("Hello", temperature=0)
    assert first.text == "response-1"
    assert second.text == "response-1"
    assert second.metadata["cache_hit"] is True
    assert completions.call_count == 1

    provider.generate_content("Hello", tools=[{"name": "lookup"}])
    provider.generate_content("Hello", tools=[{"name": "lookup"}])
    assert completions.call_count == 3
    cache.close()


@pytest.mark.asyncio
async def test_openai_stream_accepts_sync_iterables():
    provider = OpenAIProvider(OpenAIConfig(model_id="gpt-test", api_key="fake"))

    class CloseableIterator:
        def __init__(self) -> None:
            self.items = iter([openai_stream_chunk("hel"), openai_stream_chunk("lo")])
            self.closed = False

        def __iter__(self) -> "CloseableIterator":
            return self

        def __next__(self) -> Any:
            return next(self.items)

        def close(self) -> None:
            self.closed = True

    stream = CloseableIterator()

    class FakeAsyncCompletions:
        async def create(self, **kwargs: Any) -> Any:
            assert kwargs["stream"] is True
            return stream

    provider.client = SimpleNamespace(  # type: ignore[assignment]
        chat=SimpleNamespace(completions=FakeAsyncCompletions())
    )

    chunks = [chunk async for chunk in provider.stream("prompt")]

    deltas = [chunk["contentBlockDelta"]["delta"]["text"] for chunk in chunks if "contentBlockDelta" in chunk]
    assert deltas == ["hel", "lo"]
    assert chunks[-1] == {"messageStop": {"stopReason": "end_turn"}}
    assert stream.closed is True


@pytest.mark.asyncio
async def test_openai_stream_cancellation_propagates_to_async_iterator():
    provider = OpenAIProvider(OpenAIConfig(model_id="gpt-test", api_key="fake"))
    first_chunk_seen = asyncio.Event()

    class CancellableStream:
        def __init__(self) -> None:
            self.index = 0
            self.cancelled = False

        def __aiter__(self) -> "CancellableStream":
            return self

        async def __anext__(self) -> Any:
            if self.index == 0:
                self.index += 1
                return openai_stream_chunk("first")
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                self.cancelled = True
                raise
            raise StopAsyncIteration

    stream = CancellableStream()

    class FakeAsyncCompletions:
        async def create(self, **kwargs: Any) -> Any:
            assert kwargs["stream"] is True
            return stream

    provider.client = SimpleNamespace(  # type: ignore[assignment]
        chat=SimpleNamespace(completions=FakeAsyncCompletions())
    )

    async def consume() -> None:
        async for _ in provider.stream("prompt"):
            first_chunk_seen.set()

    task = asyncio.create_task(consume())
    await asyncio.wait_for(first_chunk_seen.wait(), timeout=1.0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert stream.cancelled is True


class FakeTokenized(dict):
    def to(self, device: str) -> "FakeTokenized":
        self["device"] = device
        return self


class FakeTokenizer:
    def __call__(self, prompt: str, return_tensors: str) -> FakeTokenized:
        return FakeTokenized(input_ids=[1], prompt=prompt, return_tensors=return_tensors)

    def encode(self, text: str) -> list[int]:
        return list(range(len(text.split())))


class FakeTextIteratorStreamer:
    def __init__(self, tokenizer: FakeTokenizer, skip_prompt: bool, skip_special_tokens: bool, timeout: float) -> None:
        self.timeout = timeout
        self.items: queue.Queue[Any] = queue.Queue()

    def __iter__(self) -> "FakeTextIteratorStreamer":
        return self

    def __next__(self) -> str:
        item = self.items.get(timeout=self.timeout)
        if item is StopIteration:
            raise StopIteration
        return item

    def put(self, item: str) -> None:
        self.items.put(item)

    def on_finalized_text(self, text: str, stream_end: bool = False) -> None:
        if text:
            self.items.put(text)
        if stream_end:
            self.items.put(StopIteration)


class FakeStoppingCriteria:
    pass


class FakeStoppingCriteriaList(list):
    def __call__(self, input_ids: Any, scores: Any) -> bool:
        return any(criteria(input_ids, scores) for criteria in self)


class FakeHFModel:
    device = "cpu"

    def __init__(self, delay: float = 0.03) -> None:
        self.delay = delay
        self.cancel_observed = threading.Event()
        self.done = threading.Event()

    def generate(self, streamer: FakeTextIteratorStreamer, stopping_criteria: FakeStoppingCriteriaList, **kwargs: Any) -> None:
        try:
            for i in range(kwargs["max_new_tokens"]):
                if stopping_criteria(None, None):
                    self.cancel_observed.set()
                    break
                time.sleep(self.delay)
                streamer.put(str(i))
        finally:
            streamer.on_finalized_text("", stream_end=True)
            self.done.set()


@pytest.fixture
def fake_transformers(monkeypatch):
    module = ModuleType("transformers")
    module.TextIteratorStreamer = FakeTextIteratorStreamer  # type: ignore[attr-defined]
    module.StoppingCriteria = FakeStoppingCriteria  # type: ignore[attr-defined]
    module.StoppingCriteriaList = FakeStoppingCriteriaList  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "transformers", module)


def make_hf_provider(model: FakeHFModel) -> HuggingFaceProvider:
    provider = HuggingFaceProvider(HFConfig(model_id="fake-hf"))
    provider._is_initialized = True
    provider._tokenizer = FakeTokenizer()
    provider._model = model
    return provider


@pytest.mark.asyncio
async def test_hf_stream_does_not_block_event_loop(fake_transformers):
    provider = make_hf_provider(FakeHFModel(delay=0.05))
    stream = provider.stream("prompt", max_new_tokens=2).__aiter__()
    sleep_task = asyncio.create_task(asyncio.sleep(0.01))

    first = await anext(stream)
    assert sleep_task.done()
    chunks = [first]
    async for chunk in stream:
        chunks.append(chunk)

    assert [chunk["contentBlockDelta"]["delta"]["text"] for chunk in chunks if "contentBlockDelta" in chunk] == ["0", "1"]


@pytest.mark.asyncio
async def test_hf_stream_cancellation_signals_generation(fake_transformers):
    model = FakeHFModel(delay=0.02)
    provider = make_hf_provider(model)

    async def consume() -> None:
        async for _ in provider.stream("prompt", max_new_tokens=100):
            await asyncio.sleep(0)

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert await asyncio.to_thread(model.cancel_observed.wait, 1.0)


@pytest.mark.asyncio
async def test_llamacpp_async_initialization_is_locked_and_offloaded(monkeypatch):
    class FakeLlama:
        init_count = 0
        init_lock = threading.Lock()

        def __init__(self, **_: Any) -> None:
            time.sleep(0.05)
            with self.init_lock:
                type(self).init_count += 1

        def __call__(self, prompt: str, **_: Any) -> dict:
            return {
                "choices": [{"text": f"ok:{prompt}"}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }

    module = ModuleType("llama_cpp")
    module.Llama = FakeLlama  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "llama_cpp", module)

    provider = LlamaCppProvider(LlamaCppConfig(model_id="fake.gguf"))
    sleep_task = asyncio.create_task(asyncio.sleep(0.01))
    first, second = await asyncio.gather(
        provider.generate_content_async("one"),
        provider.generate_content_async("two"),
    )

    assert sleep_task.done()
    assert first.text == "ok:one"
    assert second.text == "ok:two"
    assert FakeLlama.init_count == 1


@pytest.mark.asyncio
async def test_llamacpp_stream_closes_sync_iterator_on_consumer_close():
    class CloseAwareStream:
        def __init__(self) -> None:
            self.closed = False
            self.index = 0

        def __iter__(self) -> "CloseAwareStream":
            return self

        def __next__(self) -> dict[str, Any]:
            if self.index == 0:
                self.index += 1
                return {"choices": [{"text": "token"}]}
            raise StopIteration

        def close(self) -> None:
            self.closed = True

    stream = CloseAwareStream()

    class FakeLlama:
        def __call__(self, *_: Any, **__: Any) -> CloseAwareStream:
            return stream

    provider = LlamaCppProvider(LlamaCppConfig(model_id="fake.gguf"))
    provider._is_initialized = True
    provider._llm = FakeLlama()

    iterator = provider.stream([{"role": "user", "content": "hi"}]).__aiter__()
    assert await anext(iterator) == {"contentBlockDelta": {"delta": {"text": "token"}}}
    await iterator.aclose()

    assert stream.closed is True


@pytest.mark.asyncio
async def test_vllm_stream_unsupported_is_provider_error():
    provider = VLLMProvider(VLLMConfig(model_id="fake-vllm"))

    with pytest.raises(ProviderError, match="does not support streaming"):
        await anext(provider.stream([{"role": "user", "content": "hi"}]).__aiter__())
