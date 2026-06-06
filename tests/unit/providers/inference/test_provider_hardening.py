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
from types import SimpleNamespace
from typing import Any

import pytest

from xrtm.forecast.core.cache import InferenceCache
from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.providers.inference.openai_provider import OpenAIProvider


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
