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

r"""Unit tests for forecast.core.verification."""

import json

from forecast.core.schemas.graph import BaseGraphState
from forecast.core.verification import SovereigntyVerifier


class TestSovereigntyVerifier:
    r"""Tests for the SovereigntyVerifier class."""

    def _create_valid_manifest(self):
        r"""Create a valid manifest for testing."""
        state = BaseGraphState(
            subject_id="TEST_SUBJECT",
            node_reports={"step1": "data1"},
            execution_path=["step1"],
        )
        return {
            "version": "1.0.0",
            "subject_id": "TEST_SUBJECT",
            "final_state_hash": state.compute_hash(),
            "reasoning_trace": {"step1": "data1"},
            "execution_path": ["step1"],
            "context": {},
        }

    def test_verify_manifest_valid(self):
        r"""Should return True for valid manifest."""
        manifest = self._create_valid_manifest()
        success, errors = SovereigntyVerifier.verify_manifest(manifest)
        assert success is True
        assert errors == []

    def test_verify_manifest_missing_version(self):
        r"""Should fail when version is missing."""
        manifest = self._create_valid_manifest()
        del manifest["version"]
        success, errors = SovereigntyVerifier.verify_manifest(manifest)
        assert success is False
        assert "Missing required manifest field: version" in errors

    def test_verify_manifest_missing_subject_id(self):
        r"""Should fail when subject_id is missing."""
        manifest = self._create_valid_manifest()
        del manifest["subject_id"]
        success, errors = SovereigntyVerifier.verify_manifest(manifest)
        assert success is False
        assert "Missing required manifest field: subject_id" in errors

    def test_verify_manifest_missing_final_state_hash(self):
        r"""Should fail when final_state_hash is missing."""
        manifest = self._create_valid_manifest()
        del manifest["final_state_hash"]
        success, errors = SovereigntyVerifier.verify_manifest(manifest)
        assert success is False
        assert "Missing required manifest field: final_state_hash" in errors

    def test_verify_manifest_missing_reasoning_trace(self):
        r"""Should fail when reasoning_trace is missing."""
        manifest = self._create_valid_manifest()
        del manifest["reasoning_trace"]
        success, errors = SovereigntyVerifier.verify_manifest(manifest)
        assert success is False
        assert "Missing required manifest field: reasoning_trace" in errors

    def test_verify_manifest_hash_mismatch(self):
        r"""Should fail when hash doesn't match content."""
        manifest = self._create_valid_manifest()
        manifest["final_state_hash"] = "wrong_hash_value"
        success, errors = SovereigntyVerifier.verify_manifest(manifest)
        assert success is False
        assert any("Merkle Integrity Failure" in e for e in errors)

    def test_verify_manifest_reconstruction_error(self):
        r"""Should fail gracefully on reconstruction error."""
        manifest = {
            "version": "1.0.0",
            "subject_id": "TEST",
            "final_state_hash": "hash",
            "reasoning_trace": "invalid_not_dict",  # Should be dict
            "execution_path": None,  # Should be list
        }
        success, errors = SovereigntyVerifier.verify_manifest(manifest)
        assert success is False
        assert any("Reconstruction failed" in e for e in errors)

    def test_verify_file_valid(self, tmp_path):
        r"""Should return True for valid .xrtm file."""
        manifest = self._create_valid_manifest()
        filepath = tmp_path / "test.xrtm"
        with open(filepath, "w") as f:
            json.dump(manifest, f)

        result = SovereigntyVerifier.verify_file(str(filepath))
        assert result is True

    def test_verify_file_invalid(self, tmp_path):
        r"""Should return False for invalid .xrtm file."""
        filepath = tmp_path / "invalid.xrtm"
        with open(filepath, "w") as f:
            json.dump({"incomplete": "manifest"}, f)

        result = SovereigntyVerifier.verify_file(str(filepath))
        assert result is False

    def test_verify_file_not_found(self):
        r"""Should return False for nonexistent file."""
        result = SovereigntyVerifier.verify_file("/nonexistent/path.xrtm")
        assert result is False

    def test_verify_file_invalid_json(self, tmp_path):
        r"""Should return False for invalid JSON."""
        filepath = tmp_path / "bad.xrtm"
        with open(filepath, "w") as f:
            f.write("not valid json {")

        result = SovereigntyVerifier.verify_file(str(filepath))
        assert result is False
