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

r"""
Demo: The Centaur Protocol.
Demonstrates human-AI collaborative forecasting with the Analyst Workbench.
"""

import asyncio
import logging

from xrtm.forecast.kit.eval.workbench import AnalystWorkbench

from xrtm.forecast.core.interfaces import HumanProvider
from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.kit.agents.llm import LLMAgent

logging.basicConfig(level=logging.INFO)


class CLIHumanProvider(HumanProvider):
    r"""Simple CLI-based human provider for the demo."""

    async def get_human_input(self, prompt: str) -> str:
        print("\n[HUMAN INTERVENTION REQUIRED]")
        print(f"MESSAGE: {prompt}")
        # In a real async env, we'd use an async input,
        # but for this CLI demo, we'll block the thread for simplicity.
        val = input("YOUR REASONING: ")
        return val


class MockResearchAgent(LLMAgent):
    r"""Mock agent that provides deterministic research."""

    async def run(self, state: BaseGraphState, *args, **kwargs) -> str:
        return f"Research from {self.name}: AI is progressing 20% faster than estimated."


async def run_centaur_demo() -> None:
    r"""Run the Centaur Protocol demo with mock agents and CLI human input."""
    print("--- [THE CENTAUR PROTOCOL DEMO] ---")

    # 1. Setup Agents
    a1 = MockResearchAgent(model=None, name="Agent_Alpha")
    a2 = MockResearchAgent(model=None, name="Agent_Beta")

    # 2. Setup Workbench
    prompt = "Review the combined research from Alpha and Beta. Provide the final probability (0-1) for 'Artificial General Intelligence by 2030'."
    workbench = AnalystWorkbench(agents=[a1, a2])
    orch = workbench.build_orchestrator(reviewer_prompt=prompt)

    # 3. Setup State and Provider
    state = BaseGraphState(subject_id="AGI-2030")
    state.context["human_provider"] = CLIHumanProvider()

    # 4. Execute
    print("\nStarting AI Research Phase...")
    final_state = await orch.run(state)

    print("\n--- [CENTAUR FORECAST FINALIZED] ---")
    print(f"Subject: {final_state.subject_id}")
    print(f"Human Input: {final_state.node_reports.get(f'human:{prompt}')}")
    print(f"Merkle Hash: {final_state.state_hash[:16]}...")
    print(f"Audit Trail: {' -> '.join(final_state.execution_path)}")


if __name__ == "__main__":
    asyncio.run(run_centaur_demo())
