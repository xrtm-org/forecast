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
from typing import Any, cast

import pytest
from pydantic import SecretStr

from forecast.graph.orchestrator import Orchestrator
from forecast.inference.config import GeminiConfig, OpenAIConfig
from forecast.inference.factory import ModelFactory
from forecast.schemas.graph import BaseGraphState


def mock_tool(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b


# Give it a tool_spec like the providers expect
mock_tool_any = cast(Any, mock_tool)
mock_tool_any.tool_spec = {
    "name": "mock_tool",
    "description": "Adds two numbers.",
    "parameters": {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    },
}


async def run_complex_test(provider_name: str, config):
    r"""
    Runs a suite of complex integration tests (logprobs, tool calling) against a live provider.

    Args:
        provider_name (`str`): The name of the provider (e.g. OpenAI, Gemini).
        config: The provider configuration object.
    """
    print(f"\n🚀 Testing {provider_name} with Complex Features...")
    provider = ModelFactory.get_provider(config)

    # 1. Test Logprobs
    print(f"📊 [{provider_name}] Testing Logprobs...")
    try:
        res = await provider.generate_content_async("Pick a random number between 1 and 100", output_logprobs=True)
        if res.logprobs:
            print(f"✅ [{provider_name}] Logprobs extracted: {res.logprobs[:3]}...")
        else:
            print(f"⚠️ [{provider_name}] No logprobs returned (might not be supported by this specific model/setting)")
    except Exception as e:
        print(f"❌ [{provider_name}] Logprobs failed: {e}")

    # 2. Test Tool Calling
    print(f"🛠️ [{provider_name}] Testing Tool Calling...")
    try:
        # We ask it to use the tool
        res = await provider.generate_content_async(
            "Use the mock_tool to add 123 and 456. Tell me the final sum.", tools=[mock_tool]
        )
        # Check if tool calls were detected in raw response
        if provider_name == "OpenAI":
            if hasattr(res.raw, "choices") and res.raw.choices[0].message.tool_calls:
                print(f"✅ [{provider_name}] Tool call generated successfully.")
            else:
                print(f"⚠️ [{provider_name}] Tool call NOT generated. Response: {res.text}")
        elif provider_name == "Gemini":
            if "579" in res.text:
                print(f"✅ [{provider_name}] Tool EXECUTED and RESOLVED correctly. Result: {res.text}")
            else:
                print(f"⚠️ [{provider_name}] Tool result NOT found in final text. Response: {res.text}")
    except Exception as e:
        print(f"❌ [{provider_name}] Tool call failed: {e}")


@pytest.mark.asyncio
async def test_orchestrator_live():
    r"""
    Smoke test for the Orchestrator using a live LLM provider.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("⏭️ Skipping Orchestrator live test (OPENAI_API_KEY not set)")
        return

    print("\n🧠 Testing Orchestrator Live with OpenAI...")
    from forecast.inference.config import OpenAIConfig

    config = OpenAIConfig(model_id="gpt-4o-mini", api_key=SecretStr(openai_key))
    provider = ModelFactory.get_provider(config)

    from forecast.graph.config import GraphConfig
    graph_config = GraphConfig(max_cycles=3)
    orchestrator = Orchestrator(config=graph_config)

    async def hello_node(state: BaseGraphState, on_progress) -> str:
        res = await provider.generate_content_async("Say 'Node 1 reached'.")
        state.context["node_1"] = res.text
        return "end"

    async def end_node(state: BaseGraphState, on_progress) -> None:
        return None

    orchestrator.register_node("start", hello_node)
    orchestrator.register_node("end", end_node)

    state = BaseGraphState(subject_id="live_orchestration_test")
    await orchestrator.run(state, entry_node="start")

    if "Node 1" in state.context.get("node_1", ""):
        print(f"✅ Orchestrator successfully ran live node. Cycle count: {state.cycle_count}")
    else:
        print(f"❌ Orchestrator failed or returned unexpected text: {state.context.get('node_1')}")


async def main():
    # Load keys
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    if openai_key:
        oa_config = OpenAIConfig(model_id="gpt-4o-mini", api_key=SecretStr(openai_key))
        await run_complex_test("OpenAI", oa_config)
        await test_orchestrator_live(openai_key)

    if gemini_key:
        # Use flash for speed
        ge_config = GeminiConfig(model_id="gemini-2.0-flash-lite", api_key=SecretStr(gemini_key), redis_url=redis_url)
        await run_complex_test("Gemini", ge_config)


if __name__ == "__main__":
    asyncio.run(main())
