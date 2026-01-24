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

r"""Unit tests for InferenceCache."""

from __future__ import annotations

from xrtm.forecast.core.cache import InferenceCache


class TestInferenceCacheBasics:
    r"""Test basic cache operations."""

    def test_compute_key_deterministic(self, tmp_path):
        r"""Same inputs should produce same key."""
        cache = InferenceCache(db_path=str(tmp_path / "test.db"))
        key1 = cache.compute_key("gemini", "Hello world", temperature=0.5)
        key2 = cache.compute_key("gemini", "Hello world", temperature=0.5)
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex length
        cache.close()

    def test_compute_key_normalized_whitespace(self, tmp_path):
        r"""Whitespace differences should not affect key."""
        cache = InferenceCache(db_path=str(tmp_path / "test.db"))
        key1 = cache.compute_key("gemini", "Hello   world", temperature=0.5)
        key2 = cache.compute_key("gemini", "Hello world", temperature=0.5)
        assert key1 == key2
        cache.close()

    def test_compute_key_different_inputs(self, tmp_path):
        r"""Different inputs should produce different keys."""
        cache = InferenceCache(db_path=str(tmp_path / "test.db"))
        key1 = cache.compute_key("gemini", "Hello", temperature=0.5)
        key2 = cache.compute_key("gemini", "Hello", temperature=0.7)
        key3 = cache.compute_key("gpt-4", "Hello", temperature=0.5)
        assert key1 != key2
        assert key1 != key3
        cache.close()

    def test_set_and_get(self, tmp_path):
        r"""Basic set and get operations."""
        cache = InferenceCache(db_path=str(tmp_path / "test.db"))
        key = cache.compute_key("gemini", "What is 2+2?")
        cache.set(key, "4", {"tokens": 1})
        result = cache.get(key)
        assert result == "4"
        cache.close()

    def test_get_nonexistent_key(self, tmp_path):
        r"""Getting nonexistent key returns None."""
        cache = InferenceCache(db_path=str(tmp_path / "test.db"))
        result = cache.get("nonexistent_key_abc123")
        assert result is None
        cache.close()

    def test_clear(self, tmp_path):
        r"""Clear removes all entries."""
        cache = InferenceCache(db_path=str(tmp_path / "test.db"))
        for i in range(5):
            key = cache.compute_key("gemini", f"prompt_{i}")
            cache.set(key, f"response_{i}")

        count = cache.clear()
        assert count == 5

        # Verify all cleared
        for i in range(5):
            key = cache.compute_key("gemini", f"prompt_{i}")
            assert cache.get(key) is None
        cache.close()

    def test_stats(self, tmp_path):
        r"""Stats returns correct information."""
        cache = InferenceCache(db_path=str(tmp_path / "test.db"))
        key = cache.compute_key("gemini", "test")
        cache.set(key, "response")

        stats = cache.stats()
        assert stats["enabled"] is True
        assert stats["entry_count"] == 1
        assert stats["total_size_bytes"] > 0
        cache.close()


class TestInferenceCacheDisabled:
    r"""Test cache when disabled."""

    def test_disabled_by_constructor(self, tmp_path):
        r"""Cache disabled via constructor."""
        cache = InferenceCache(db_path=str(tmp_path / "test.db"), enabled=False)
        key = cache.compute_key("gemini", "test")
        cache.set(key, "response")
        result = cache.get(key)
        assert result is None
        cache.close()

    def test_disabled_stats(self, tmp_path):
        r"""Stats when disabled."""
        cache = InferenceCache(db_path=str(tmp_path / "test.db"), enabled=False)
        stats = cache.stats()
        assert stats["enabled"] is False
        cache.close()


class TestInferenceCacheEviction:
    r"""Test LRU eviction."""

    def test_eviction_when_over_limit(self, tmp_path):
        r"""Entries are evicted when cache exceeds max size."""
        # Set max size to 100 bytes
        cache = InferenceCache(db_path=str(tmp_path / "test.db"), max_size_bytes=100)

        # Add entries that exceed limit
        for i in range(10):
            key = cache.compute_key("gemini", f"prompt_{i}")
            cache.set(key, "x" * 20)  # 20 bytes each

        # Check that some entries were evicted
        stats = cache.stats()
        assert stats["total_size_bytes"] <= 100
        cache.close()
