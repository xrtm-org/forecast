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
from datetime import datetime, timezone

import pytest

from xrtm.forecast.core.memory.graph import Fact
from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.core.utils.bundling import ForecastBundle
from xrtm.forecast.kit.agents.llm import LLMAgent
from xrtm.forecast.kit.agents.specialists.adversary import AdversaryAgent
from xrtm.forecast.kit.stages.bayesian import BayesianSieveStage
from xrtm.forecast.providers.memory.sqlite_kg import SQLiteFactStore


@pytest.mark.asyncio
async def test_consensus_lab_integration():
    print("--- Starting Consensus Lab Integration Test ---")

    # 1. Setup FactStore
    db_path = "test_memory.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    fact_store = SQLiteFactStore(db_path)
    test_fact = Fact(
        subject="ConsensusLab", predicate="status", object_value="Active", verified_at=datetime.now(timezone.utc)
    )
    await fact_store.remember(test_fact)

    # 2. Verify FactStore Query
    facts = await fact_store.query("ConsensusLab")
    assert len(facts) == 1
    assert facts[0].object_value == "Active"
    print("[PASS] FactStore: Persistence and Query verified.")

    # 3. Setup Bayesian Sieve
    # We'll use a mock-like agent setup for deterministic BF
    class MockAgent(LLMAgent):
        async def run(self, input_data, context=None, **kwargs):
            from xrtm.forecast.providers.inference.base import ModelResponse

            # Simulate returning a Bayes Factor in metadata
            return ModelResponse(text="Evidence is supportive.", metadata={"bayes_factor": 1.5})

    mock_agent = MockAgent(model=None)  # Model not needed for this mock
    sieve = BayesianSieveStage(agent=mock_agent, prior_key="base_rate", output_key="final_forecast")

    state = BaseGraphState(subject_id="test_bayesian")
    state.context["base_rate"] = 0.2

    state = await sieve(state)
    assert 0.27 < state.context["final_forecast"] < 0.28
    print(f"[PASS] BayesianSieve: 0.2 prior -> {state.context['final_forecast']:.4f} posterior.")

    # 4. Verify AdversaryAgent (Red-Team)
    # We'll just verify it can be instantiated and has the right persona
    adversary = AdversaryAgent(model=None)
    assert "Red Team" in adversary.persona
    print("[PASS] AdversaryAgent: Persona verified.")

    # 5. Test .forecast Bundling
    bundle_path = "test_run.forecast"
    if os.path.exists(bundle_path):
        os.remove(bundle_path)

    ForecastBundle.create(state, bundle_path, evidence={"source.txt": "Fact: Consensus is active."})
    assert os.path.exists(bundle_path)

    bundle = ForecastBundle(bundle_path)
    verification = bundle.verify()
    assert verification["is_valid"]
    print("[PASS] ForecastBundle: Creation and Verification verified.")

    # cleanup
    os.remove(db_path)
    os.remove(bundle_path)
    print("\n--- CONSENSUS LAB INTEGRATION SUCCESS ---")


if __name__ == "__main__":
    asyncio.run(test_consensus_lab_integration())
