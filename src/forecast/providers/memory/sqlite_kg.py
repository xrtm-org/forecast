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
Reference implementation of FactStore using a local SQLite database.
r"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional

from forecast.core.memory.graph import Fact, FactStore


class SQLiteFactStore(FactStore):
    r"""
    A local Knowledge Graph implementation backed by SQLite.

    This is suitable for institutional memory that needs to be
    persistent, shared via git-tracked files, and low-latency.
    r"""

    def __init__(self, db_path: str = "memory.db"):
        r"""
        Initializes the SQLiteFactStore.

        Args:
            db_path (`str`): Path to the SQLite database file.
        r"""
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                r"""
                CREATE TABLE IF NOT EXISTS facts (
                    subject TEXT,
                    predicate TEXT,
                    object_value TEXT,
                    source_url TEXT,
                    source_hash TEXT,
                    verified_at TEXT,
                    expires_at TEXT,
                    confidence REAL,
                    PRIMARY KEY (subject, predicate)
                )
                """
            )
            conn.commit()

    async def remember(self, fact: Fact) -> None:
        r"""Stores a fact in the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO facts
                (subject, predicate, object_value, source_url, source_hash, verified_at, expires_at, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fact.subject,
                    fact.predicate,
                    json.dumps(fact.object_value),
                    fact.source_url,
                    fact.source_hash,
                    fact.verified_at.isoformat(),
                    fact.expires_at.isoformat() if fact.expires_at else None,
                    fact.confidence,
                ),
            )
            conn.commit()

    async def query(self, subject: str, predicate: Optional[str] = None) -> List[Fact]:
        r"""Queries facts from the database."""
        query = "SELECT * FROM facts WHERE subject = ?"
        params = [subject]

        if predicate:
            query += " AND predicate = ?"
            params.append(predicate)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

            facts = []
            for row in rows:
                facts.append(
                    Fact(
                        subject=row["subject"],
                        predicate=row["predicate"],
                        object_value=json.loads(row["object_value"]),
                        source_url=row["source_url"],
                        source_hash=row["source_hash"],
                        verified_at=datetime.fromisoformat(row["verified_at"]),
                        expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
                        confidence=row["confidence"],
                    )
                )
            return facts

    async def forget(self, subject: str, predicate: Optional[str] = None) -> None:
        r"""Removes facts from the database."""
        query = "DELETE FROM facts WHERE subject = ?"
        params = [subject]

        if predicate:
            query += " AND predicate = ?"
            params.append(predicate)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(query, params)
            conn.commit()


__all__ = ["SQLiteFactStore"]
