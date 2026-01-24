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

import logging
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

__all__ = ["SourceTrustEntry", "SourceTrustRegistry", "IntegrityGuardian"]


class SourceTrustEntry(BaseModel):
    r"""Represents the trust profile for a specific information source or domain."""

    domain: str
    trust_score: float = Field(ge=0.0, le=1.0, default=0.5)
    reliability_history: List[float] = Field(default_factory=list)
    tags: Set[str] = Field(default_factory=set)


class SourceTrustRegistry:
    r"""
    A registry of verified news and data domains with associated trust scores.
    Enables the 'Epistemic Security' layer of the platform.
    """

    def __init__(self, default_trust: float = 0.5):
        r"""
        Initializes the registry with a global default trust score.

        Args:
            default_trust (`float`, *optional*, defaults to `0.5`):
                The trust score to return for unknown domains.

        Example:
            ```python
            >>> registry = SourceTrustRegistry(default_trust=0.2)
            ```
        """
        self._registry: Dict[str, SourceTrustEntry] = {}
        self.default_trust = default_trust

    def register_source(self, domain: str, trust_score: float, tags: Optional[List[str]] = None):
        r"""
        Adds or updates a source in the registry.

        Args:
            domain (`str`):
                The domain name to register (e.g., "reputable.org").
            trust_score (`float`):
                Trust score between 0.0 and 1.0.
            tags (`List[str]`, *optional*):
                Metadata tags for the source.

        Example:
            ```python
            >>> registry.register_source("reputable.org", 0.9, tags=["verified"])
            ```
        """
        entry = SourceTrustEntry(domain=domain, trust_score=trust_score, tags=set(tags or []))
        self._registry[domain] = entry
        logger.info(f"[TRUST] Registered {domain} with score {trust_score}")

    def get_trust_score(self, domain: str) -> float:
        r"""
        Returns the trust score for a domain, or the default if unknown.

        Args:
            domain (`str`):
                The domain name to query.

        Returns:
            `float`: The trust score.

        Example:
            ```python
            >>> score = registry.get_trust_score("reputable.org")
            >>> print(score)
            0.9
            ```
        """
        # Simple domain matching for now
        if domain in self._registry:
            return self._registry[domain].trust_score
        return self.default_trust


class IntegrityGuardian:
    r"""
    An automated stage for filtering or flagging data based on source trust.
    Part of the 'Institutional Epistemics' layer.
    """

    def __init__(self, registry: SourceTrustRegistry, threshold: float = 0.3):
        r"""
        Initializes the guardian with a registry and blocking threshold.

        Args:
            registry (`SourceTrustRegistry`):
                The source trust registry to use for domain lookups.
            threshold (`float`, *optional*, defaults to `0.3`):
                Any domain with a trust score below this value is blocked.

        Example:
            ```python
            >>> guardian = IntegrityGuardian(registry, threshold=0.4)
            ```
        """
        self.registry = registry
        self.threshold = threshold

    async def validate_data_sources(self, sources: List[str]) -> Dict[str, List[str]]:
        r"""
        Checks a list of sources against the trust registry.

        Args:
            sources (`List[str]`):
                A list of domain names to validate.

        Returns:
            `Dict[str, List[str]]`:
                A dictionary categorizing sources into "passed", "flagged", and "blocked".

        Example:
            ```python
            >>> results = await guardian.validate_data_sources(["reputable.org", "shady.com"])
            >>> print(results["blocked"])
            ['shady.com']
            ```
        """
        results: Dict[str, List[str]] = {"passed": [], "flagged": [], "blocked": []}

        for src in sources:
            score = self.registry.get_trust_score(src)
            if score < self.threshold:
                results["blocked"].append(src)
            elif score < 0.5:
                results["flagged"].append(src)
            else:
                results["passed"].append(src)

        return results
