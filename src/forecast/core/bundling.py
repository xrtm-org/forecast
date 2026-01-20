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

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from forecast.core.schemas.graph import BaseGraphState
from forecast.version import __version__

logger = logging.getLogger(__name__)


class ManifestBundler:
    r"""
    Generates an institutional-grade research proof (.xrtm manifest).

    The manifest includes the full reasoning trace, Merkle hashes for every step,
    and system metadata to enable external verification of the forecast.
    """

    @staticmethod
    def bundle(state: BaseGraphState, extra_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        r"""
        Packages a graph state into a verifiable manifest.

        Args:
            state (`BaseGraphState`): The final state of the reasoning execution.
            extra_metadata (`Dict[str, Any]`, *optional*): Additional context (e.g., user ID, environment).

        Returns:
            `Dict[str, Any]`: The .xrtm manifest dictionary.
        """
        manifest = {
            "version": "1.0",
            "engine": f"xrtm-forecast {__version__}",
            "timestamp": datetime.now().isoformat(),
            "subject_id": state.subject_id,
            "cycle_count": state.cycle_count,
            "final_state_hash": state.state_hash,
            "execution_path": state.execution_path,
            "reasoning_trace": state.node_reports,
            "telemetry": {
                "latencies": state.latencies,
                "usage": state.usage,
            },
            "context": state.context,
            "ext_metadata": extra_metadata or {},
        }

        # Check for Merkle integrity
        if not state.state_hash:
            logger.warning("[BUNDLER] State hash is missing. Manifest is not cryptographically verifiable.")

        return manifest

    @staticmethod
    def write_to_file(manifest: Dict[str, Any], path: str) -> None:
        r"""Writes the manifest to a JSON file (standardizing on .xrtm extension)."""
        if not path.endswith(".xrtm"):
            path += ".xrtm"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True, default=str)
        logger.info(f"[BUNDLER] Verifiable research proof written to {path}")


__all__ = ["ManifestBundler"]
