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
import os

import pytest
from pydantic import SecretStr

from forecast.inference.config import GeminiConfig, OpenAIConfig
from forecast.inference.factory import ModelFactory


@pytest.mark.live
@pytest.mark.asyncio
async def test_gemini_live():
    r"""
    Smoke test for reaching the Gemini API.
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("⏭️ Skipping Gemini live test (GEMINI_API_KEY not set)")
        return

    print("🧪 Testing Gemini Live...")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    config = GeminiConfig(model_id="gemini-2.0-flash-lite", api_key=SecretStr(key), redis_url=redis_url)
    provider = ModelFactory.get_provider(config)
    try:
        response = await provider.generate_content_async("Say 'hello world' in one word.")
        print(f"✅ Gemini Response: {response.text}")
    except Exception as e:
        print(f"❌ Gemini Failed: {e}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_openai_live():
    r"""
    Smoke test for reaching the OpenAI API.
    """
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("⏭️ Skipping OpenAI live test (OPENAI_API_KEY not set)")
        return

    print("🧪 Testing OpenAI Live...")
    config = OpenAIConfig(model_id="gpt-4o-mini", api_key=SecretStr(key))
    provider = ModelFactory.get_provider(config)
    try:
        response = await provider.generate_content_async("Say 'hello world' in one word.")
        print(f"✅ OpenAI Response: {response.text}")
    except Exception as e:
        print(f"❌ OpenAI Failed: {e}")


async def main():
    await test_gemini_live()
    await test_openai_live()


if __name__ == "__main__":
    asyncio.run(main())
