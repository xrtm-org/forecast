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

import hashlib
import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AuditHasher:
    """
    Provides SHA-256 signing and verification for reasoning chains.
    Ensures that logic traces cannot be tampered with after generation.
    """

    @staticmethod
    def calculate_hash(data: Dict[str, Any]) -> str:
        """Calculates a deterministic SHA-256 hash of a dictionary."""
        # Use default=str to handle non-serializable objects
        encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def sign_log(log_dict: Dict[str, Any]) -> str:
        """Generates a signature for the given log dictionary."""
        # Strip 'signature' if it already exists
        content = {k: v for k, v in log_dict.items() if k != "signature"}
        return AuditHasher.calculate_hash(content)

    @staticmethod
    def verify_log(log_dict: Dict[str, Any]) -> bool:
        """Verifies that the signature matches content."""
        if "signature" not in log_dict:
            return False

        expected_sig = log_dict["signature"]
        actual_sig = AuditHasher.sign_log(log_dict)
        return actual_sig == expected_sig
