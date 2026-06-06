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

from xrtm.forecast.core.config.inference import OpenAIConfig
from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.providers.inference.factory import ModelFactory


def mock_tool(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b


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


async def run_complex_test(config):
    r"""Runs complex integration tests (logprobs, tool calling) against live OpenAI."""
    print("\nTesting OpenAI with Complex Features...")
    provider = ModelFactory.get_provider(config)

    print("Testing Logprobs...")
    try:
        res = await provider.generate_content_async(
            "Pick a random number between 1 and 100", output_logprobs=True
        )
        if res.logprobs:
            print(f"Logprobs extracted: {res.logprobs[:3]}...")
        else:
            print("No logprobs returned (might not be supported by this model)")
    except Exception as e:
        print(f"Logprobs failed: {e}")

    print("Testing Tool Calling...")
    try:
        res = await provider.generate_content_async(
            "Use the mock_tool to add 123 and 456. Tell me the final sum.",
            tools=[mock_tool],
        )
        if hasattr(res.raw, "choices") and res.raw.choices[0].message.tool_calls:
            print("Tool call generated successfully.")
        else:
            print(f"Tool call NOT generated. Response: {res.text}")
    except Exception as e:
        print(f"Tool call failed: {e}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_orchestrator_live():
    r"""Smoke test for the Orchestrator using a live OpenAI provider."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("Skipping Orchestrator live test (OPENAI_API_KEY not set)")
        return

    print("\nTesting Orchestrator Live with OpenAI...")
    from xrtm.forecast.core.config.graph import GraphConfig

    config = OpenAIConfig(model_id="gpt-4o-mini", api_key=SecretStr(openai_key))
    provider = ModelFactory.get_provider(config)

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
        print(f"Orchestrator successfully ran live node. Cycle count: {state.cycle_count}")
    else:
        print(f"Orchestrator failed or returned unexpected text: {state.context.get('node_1')}")


async def main():
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        oa_config = OpenAIConfig(model_id="gpt-4o-mini", api_key=SecretStr(openai_key))
        await run_complex_test(oa_config)
        await test_orchestrator_live(openai_key)


if __name__ == "__main__":
    asyncio.run(main())
