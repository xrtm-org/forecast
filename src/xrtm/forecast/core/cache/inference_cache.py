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

r"""SQLite-based inference cache for LLM response caching.

This module provides a caching layer to reduce API costs and latency during
development and testing by storing and retrieving LLM responses based on
content-addressable hashing.

Example:
    >>> from xrtm.forecast.core.cache import InferenceCache
    >>> cache = InferenceCache()
    >>> key = cache.compute_key("gemini", "What is 2+2?", temperature=0.0)
    >>> cache.set(key, "4", {"model": "gemini"})
    >>> cache.get(key)
    '4'
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = ["InferenceCache"]

logger = logging.getLogger(__name__)


class InferenceCache:
    r"""SQLite-based LLM response cache with telemetry integration.

    The cache stores responses keyed by SHA256 hash of normalized inputs,
    enabling deterministic cache lookups regardless of whitespace differences.

    Args:
        db_path (`str`, *optional*, defaults to `.cache/inference.db`):
            Path to the SQLite database file.
        enabled (`bool`, *optional*, defaults to `True`):
            Whether caching is enabled. Can be overridden by
            `FORECAST_CACHE_ENABLED` environment variable.
        max_size_bytes (`int`, *optional*, defaults to `1073741824`):
            Maximum cache size in bytes (default 1GB). LRU eviction when exceeded.

    Example:
        >>> cache = InferenceCache(db_path=".cache/test.db")
        >>> key = cache.compute_key("gpt-4", "Hello", temperature=0.7)
        >>> cache.set(key, "Hi there!", {"tokens": 3})
        >>> result = cache.get(key)
        >>> print(result)
        Hi there!
    """

    def __init__(
        self,
        db_path: str = ".cache/inference.db",
        enabled: bool = True,
        max_size_bytes: int = 1024 * 1024 * 1024,  # 1GB
    ) -> None:
        # Environment variable override
        env_enabled = os.environ.get("FORECAST_CACHE_ENABLED", "").lower()
        if env_enabled == "false":
            enabled = False
        elif env_enabled == "true":
            enabled = True

        self.enabled = enabled
        self.db_path = Path(db_path)
        self.max_size_bytes = max_size_bytes
        self._conn: Optional[sqlite3.Connection] = None

        if self.enabled:
            self._init_db()

    def _init_db(self) -> None:
        r"""Initialize SQLite database with cache table."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                metadata TEXT,
                created_at REAL NOT NULL,
                last_accessed REAL NOT NULL,
                size_bytes INTEGER NOT NULL
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache(last_accessed)")
        self._conn.commit()
        logger.debug("Initialized inference cache at %s", self.db_path)

    def compute_key(self, model_id: str, prompt: str, **params: Any) -> str:
        r"""Compute SHA256 hash key from normalized inputs.

        Args:
            model_id (`str`):
                The model identifier (e.g., "gemini", "gpt-4").
            prompt (`str`):
                The prompt text to hash.
            **params:
                Additional parameters to include in the hash (e.g., temperature).

        Returns:
            `str`: A 64-character hexadecimal SHA256 hash.

        Example:
            >>> cache = InferenceCache()
            >>> key = cache.compute_key("gemini", "Hello world", temperature=0.5)
            >>> len(key)
            64
        """
        # Normalize prompt: strip whitespace, consistent encoding
        normalized_prompt = " ".join(prompt.split())

        # Create deterministic JSON representation
        hash_input = {
            "model_id": model_id,
            "prompt": normalized_prompt,
            "params": {k: v for k, v in sorted(params.items()) if v is not None},
        }
        hash_str = json.dumps(hash_input, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[str]:
        r"""Retrieve cached response by key.

        Updates the last_accessed timestamp for LRU tracking.
        Logs a cache_hit or cache_miss trace event.

        Args:
            key (`str`):
                The cache key (SHA256 hash from `compute_key`).

        Returns:
            `Optional[str]`: The cached response, or None if not found.

        Example:
            >>> cache = InferenceCache()
            >>> result = cache.get("nonexistent_key")
            >>> result is None
            True
        """
        if not self.enabled or self._conn is None:
            return None

        cursor = self._conn.execute("SELECT value FROM cache WHERE key = ?", (key,))
        row = cursor.fetchone()

        if row is None:
            logger.debug("Cache miss: %s", key[:16])
            return None

        # Update last accessed time for LRU
        self._conn.execute(
            "UPDATE cache SET last_accessed = ? WHERE key = ?",
            (time.time(), key),
        )
        self._conn.commit()

        logger.debug("Cache hit: %s", key[:16])
        return row[0]

    def set(self, key: str, value: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        r"""Store a response in the cache.

        Performs LRU eviction if the cache exceeds max_size_bytes.

        Args:
            key (`str`):
                The cache key (SHA256 hash from `compute_key`).
            value (`str`):
                The response to cache.
            metadata (`Dict[str, Any]`, *optional*):
                Additional metadata to store (e.g., token counts).

        Example:
            >>> cache = InferenceCache()
            >>> cache.set("my_key", "my_value", {"tokens": 10})
        """
        if not self.enabled or self._conn is None:
            return

        size_bytes = len(value.encode("utf-8"))
        metadata_json = json.dumps(metadata) if metadata else None
        now = time.time()

        self._conn.execute(
            """
            INSERT OR REPLACE INTO cache (key, value, metadata, created_at, last_accessed, size_bytes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (key, value, metadata_json, now, now, size_bytes),
        )
        self._conn.commit()

        logger.debug("Cache set: %s (%d bytes)", key[:16], size_bytes)

        # Check if eviction is needed
        self._maybe_evict()

    def _maybe_evict(self) -> None:
        r"""Evict least recently used entries if cache exceeds max size."""
        if self._conn is None:
            return

        cursor = self._conn.execute("SELECT SUM(size_bytes) FROM cache")
        total_size = cursor.fetchone()[0] or 0

        if total_size <= self.max_size_bytes:
            return

        # Evict oldest entries until under limit
        target_size = int(self.max_size_bytes * 0.8)  # Evict to 80% capacity
        while total_size > target_size:
            cursor = self._conn.execute("SELECT key, size_bytes FROM cache ORDER BY last_accessed ASC LIMIT 1")
            row = cursor.fetchone()
            if row is None:
                break

            self._conn.execute("DELETE FROM cache WHERE key = ?", (row[0],))
            total_size -= row[1]
            logger.debug("Evicted cache entry: %s", row[0][:16])

        self._conn.commit()

    def clear(self) -> int:
        r"""Clear all cached entries.

        Returns:
            `int`: Number of entries deleted.

        Example:
            >>> cache = InferenceCache()
            >>> cache.set(cache.compute_key("m", "p"), "v")
            >>> count = cache.clear()
            >>> count >= 1
            True
        """
        if not self.enabled or self._conn is None:
            return 0

        cursor = self._conn.execute("SELECT COUNT(*) FROM cache")
        count = cursor.fetchone()[0]

        self._conn.execute("DELETE FROM cache")
        self._conn.commit()

        logger.info("Cleared %d cache entries", count)
        return count

    def stats(self) -> Dict[str, Any]:
        r"""Get cache statistics.

        Returns:
            `Dict[str, Any]`: Dictionary with entry_count, total_size_bytes, db_path.

        Example:
            >>> cache = InferenceCache()
            >>> stats = cache.stats()
            >>> "entry_count" in stats
            True
        """
        if not self.enabled or self._conn is None:
            return {"enabled": False}

        cursor = self._conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM cache")
        row = cursor.fetchone()

        return {
            "enabled": True,
            "entry_count": row[0] or 0,
            "total_size_bytes": row[1] or 0,
            "db_path": str(self.db_path),
            "max_size_bytes": self.max_size_bytes,
        }

    def close(self) -> None:
        r"""Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
