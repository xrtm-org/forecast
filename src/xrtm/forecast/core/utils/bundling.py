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
Reasoning Portability Utilities.
Handles the creation and verification of '.forecast' auditable bundles.
r"""

import hashlib
import json
import logging
import os
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from xrtm.forecast.core.schemas.graph import BaseGraphState
from xrtm.forecast.version import __version__

logger = logging.getLogger(__name__)


def calculate_sha256(data: str) -> str:
    r"""Calculates the SHA-256 hash of a string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class ForecastBundle:
    r"""
    A portable, auditable archive of a forecast run.
    r"""

    def __init__(self, bundle_path: str):
        self.bundle_path = bundle_path

    @classmethod
    def create(cls, state: BaseGraphState, output_path: str, evidence: Optional[Dict[str, str]] = None) -> str:
        r"""
        Creates a .forecast bundle from a graph state and evidence.
        r"""
        if not output_path.endswith(".forecast"):
            output_path += ".forecast"

        manifest: Dict[str, Any] = {
            "version": __version__,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": {},
        }

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Store Trace
            trace_data = state.model_dump_json(indent=2)
            zf.writestr("trace.json", trace_data)
            manifest["files"]["trace.json"] = calculate_sha256(trace_data)

            # 2. Store Evidence if provided
            if evidence:
                for filename, content in evidence.items():
                    # Clean filename to be safe for zip
                    safe_name = f"evidence/{os.path.basename(filename)}"
                    zf.writestr(safe_name, content)
                    manifest["files"][safe_name] = calculate_sha256(content)

            # 3. Store Environment/Metadata
            env_metadata = {
                "engine_version": __version__,
                "subject_id": state.subject_id,
                "node_count": len(state.execution_path),
            }
            env_data = json.dumps(env_metadata, indent=2)
            zf.writestr("environment.json", env_data)
            manifest["files"]["environment.json"] = calculate_sha256(env_data)

            # 4. Final Manifest
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        logger.info(f"Created .forecast bundle at {output_path}")
        return output_path

    def verify(self) -> Dict[str, Any]:
        r"""
        Verifies the integrity of the .forecast bundle.
        r"""
        results: Dict[str, Any] = {"is_valid": True, "errors": [], "metadata": {}}

        try:
            with zipfile.ZipFile(self.bundle_path, "r") as zf:
                # 1. Check Manifest
                if "manifest.json" not in zf.namelist():
                    results["is_valid"] = False
                    results["errors"].append("Missing manifest.json")
                    return results

                manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
                results["metadata"] = manifest

                # 2. Verify Hashes
                for filename, expected_hash in manifest.get("files", {}).items():
                    if filename not in zf.namelist():
                        results["is_valid"] = False
                        results["errors"].append(f"Missing file referenced in manifest: {filename}")
                        continue

                    actual_data = zf.read(filename).decode("utf-8")
                    actual_hash = calculate_sha256(actual_data)

                    if actual_hash != expected_hash:
                        results["is_valid"] = False
                        results["errors"].append(f"Hash mismatch for {filename}")

        except Exception as e:
            results["is_valid"] = False
            results["errors"].append(f"Bundle verification failed with error: {str(e)}")

        return results


__all__ = ["ForecastBundle"]
