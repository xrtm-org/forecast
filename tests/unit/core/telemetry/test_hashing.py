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

r"""Unit tests for forecast.core.telemetry.hashing."""

from xrtm.forecast.core.telemetry.hashing import AuditHasher


class TestAuditHasher:
    r"""Tests for the AuditHasher class."""

    def test_calculate_hash_deterministic(self):
        r"""Same input should produce same hash."""
        data = {"key": "value", "number": 42}
        hash1 = AuditHasher.calculate_hash(data)
        hash2 = AuditHasher.calculate_hash(data)
        assert hash1 == hash2

    def test_calculate_hash_different_data(self):
        r"""Different input should produce different hash."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        hash1 = AuditHasher.calculate_hash(data1)
        hash2 = AuditHasher.calculate_hash(data2)
        assert hash1 != hash2

    def test_calculate_hash_order_independent(self):
        r"""Key order should not affect hash (sorted keys)."""
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}
        assert AuditHasher.calculate_hash(data1) == AuditHasher.calculate_hash(data2)

    def test_calculate_hash_handles_non_serializable(self):
        r"""Should handle non-serializable objects via default=str."""

        class CustomObj:
            pass

        data = {"obj": CustomObj()}
        # Should not raise
        hash_val = AuditHasher.calculate_hash(data)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA-256 hex length

    def test_sign_log_strips_existing_signature(self):
        r"""Should strip existing signature before signing."""
        log = {"data": "value", "signature": "old_signature"}
        sig = AuditHasher.sign_log(log)

        # Signature should be based on content without signature field
        expected_sig = AuditHasher.calculate_hash({"data": "value"})
        assert sig == expected_sig

    def test_verify_log_valid(self):
        r"""Should verify valid signature."""
        log = {"data": "value"}
        log["signature"] = AuditHasher.sign_log(log)

        assert AuditHasher.verify_log(log) is True

    def test_verify_log_invalid(self):
        r"""Should reject tampered data."""
        log = {"data": "value"}
        log["signature"] = AuditHasher.sign_log(log)

        # Tamper with data
        log["data"] = "tampered"

        assert AuditHasher.verify_log(log) is False

    def test_verify_log_missing_signature(self):
        r"""Should return False when signature is missing."""
        log = {"data": "value"}
        assert AuditHasher.verify_log(log) is False
