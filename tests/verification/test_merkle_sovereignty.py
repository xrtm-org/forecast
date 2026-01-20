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

import os
from typing import Any, Optional

import pytest

from forecast.core.bundling import ManifestBundler
from forecast.core.orchestrator import Orchestrator
from forecast.core.schemas.graph import BaseGraphState
from forecast.core.verification import SovereigntyVerifier


@pytest.mark.asyncio
async def test_merkle_reasoning_and_bundling(tmp_path):
    r"""
    Verifies that the Orchestrator correctly anchors state transitions with Merkle hashes
    and that the ManifestBundler creates a verifiable .xrtm proof.
    """
    # 1. Setup Orchestrator
    orch = Orchestrator.create_standard(max_cycles=5)

    async def step_one(state: BaseGraphState, on_progress: Optional[Any] = None) -> str:
        state.node_reports["step_one"] = {"data": "A"}
        return "step_two"

    async def step_two(state: BaseGraphState, on_progress: Optional[Any] = None) -> None:
        state.node_reports["step_two"] = {"data": "B"}
        return None

    orch.add_node("step_one", step_one)
    orch.add_node("step_two", step_two)
    orch.set_entry_point("step_one")

    # 2. Run execution
    state = BaseGraphState(subject_id="merkle-test-01")
    assert state.state_hash is None
    assert state.parent_hash is None

    final_state = await orch.run(state)

    # 3. Verify Merkle Chain
    assert final_state.state_hash is not None, "Final state hash should be computed"
    assert final_state.parent_hash is not None, "Parent hash should be anchored from the penultimate step"
    assert final_state.state_hash != final_state.parent_hash

    # Verification of determinism: Re-computing hash manually should match
    expected_hash = final_state.compute_hash()
    assert final_state.state_hash == expected_hash

    # 4. Verify Bundling
    manifest = ManifestBundler.bundle(final_state, extra_metadata={"origin": "pytest"})
    assert manifest["subject_id"] == "merkle-test-01"
    assert manifest["final_state_hash"] == final_state.state_hash
    assert "step_one" in manifest["reasoning_trace"]
    assert "step_two" in manifest["reasoning_trace"]
    assert manifest["ext_metadata"]["origin"] == "pytest"

    # 5. Verify File Serialization
    manifest_path = str(tmp_path / "proof_01.xrtm")
    ManifestBundler.write_to_file(manifest, manifest_path)
    assert os.path.exists(manifest_path)

    with open(manifest_path, "r") as f:
        import json

        loaded = json.load(f)
        assert loaded["final_state_hash"] == final_state.state_hash

    # 6. Verify with SovereigntyVerifier
    v_success, v_errors = SovereigntyVerifier.verify_manifest(manifest)
    assert v_success, f"Sovereignty verification failed: {v_errors}"
    print("Verification utility check PASSED.")

    print(">>> Merkle Sovereignty Verification SUCCESS!")
