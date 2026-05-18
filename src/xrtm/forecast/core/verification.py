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

r"""Research proof verification.

Provides ``SovereigntyVerifier`` for validating the cryptographic
integrity of ``.xrtm`` manifest files, checking structural completeness,
hash consistency, and reasoning chain coherence.
"""

import json
import logging
from typing import Any, Dict, List, Tuple

from xrtm.forecast.core.schemas.graph import BaseGraphState

logger = logging.getLogger(__name__)


class SovereigntyVerifier:
    r"""
    A utility for verifying the cryptographic integrity of .xrtm research proofs.
    """

    @staticmethod
    def verify_manifest(manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []

        # 1. Structural Check
        required = ["version", "subject_id", "final_state_hash", "reasoning_trace"]
        for field in required:
            if field not in manifest:
                errors.append(f"Missing required manifest field: {field}")

        if errors:
            return False, errors

        execution_trace = manifest.get("execution_trace", manifest.get("execution_path"))
        if execution_trace is None:
            errors.append("Missing required manifest field: execution_trace")
            return False, errors

        # 2. Re-compute Merkle Hash of the final state
        try:
            state = BaseGraphState(
                subject_id=manifest["subject_id"],
                node_reports=manifest["reasoning_trace"],
                execution_trace=execution_trace,
                cycle_count=manifest.get("cycle_count", 0),
            )
            state.context = manifest.get("context", {})

            reputed_hash = manifest["final_state_hash"]
            actual_hash = state.compute_hash()

            if reputed_hash != actual_hash:
                errors.append(
                    f"Merkle Integrity Failure: manifest hash {reputed_hash} != calculated hash {actual_hash}"
                )

        except Exception as e:
            errors.append(f"Reconstruction failed: {e}")

        return len(errors) == 0, errors

    @staticmethod
    def verify_file(path: str) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            success, errors = SovereigntyVerifier.verify_manifest(manifest)
            if not success:
                for err in errors:
                    logger.error(f"[VERIFIER] {err}")
            return success
        except Exception as e:
            logger.error(f"[VERIFIER] Failed to read or parse file: {e}")
            return False


__all__ = ["SovereigntyVerifier"]
