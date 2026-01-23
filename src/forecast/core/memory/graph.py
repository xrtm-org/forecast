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
Core interfaces for Sovereign Knowledge Graphs (Institutional Memory).
r"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Fact(BaseModel):
    r"""
    A single fact stored in the Knowledge Graph.
    r"""

    subject: str = Field(description="The entity the fact is about (e.g., 'Tesla').")
    predicate: str = Field(description="The relationship (e.g., 'revenue_2024').")
    object_value: Any = Field(description="The value of the fact.")
    source_url: Optional[str] = Field(default=None, description="Where the fact came from.")
    source_hash: Optional[str] = Field(default=None, description="SHA-256 hash of the evidence.")
    verified_at: datetime = Field(default_factory=datetime.utcnow, description="When the fact was confirmed.")
    expires_at: Optional[datetime] = Field(default=None, description="When the fact should be considered stale.")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the fact truthfulness.")

    @property
    def is_stale(self) -> bool:
        r"""Checks if the fact has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


class FactStore(ABC):
    r"""
    Abstract interface for local institutional memory.
    r"""

    @abstractmethod
    async def remember(self, fact: Fact) -> None:
        r"""
        Stores a fact in the knowledge graph.

        Args:
            fact (`Fact`): The fact object to store.
        r"""
        pass

    @abstractmethod
    async def query(self, subject: str, predicate: Optional[str] = None) -> List[Fact]:
        r"""
        Queries facts about a subject.

        Args:
            subject (`str`): The entity to query.
            predicate (`str`, *optional*): The specific relationship to filter by.

        Returns:
            `List[Fact]`: A list of matching facts.
        r"""
        pass

    @abstractmethod
    async def forget(self, subject: str, predicate: Optional[str] = None) -> None:
        r"""
        Removes facts from the store.
        r"""
        pass


__all__ = ["Fact", "FactStore"]
