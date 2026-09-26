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

r"""Zero-dependency lexical retrieval (BM25) over document collections.

For archive search and dedup without embedding models: tokenise documents,
score with BM25, and return the top-k matches. An embedding backend can be
plugged in behind the same ``search(query, k)`` shape later.

Example:
    >>> from xrtm.forecast.kit.skills.retrieval import LexicalRetriever
    >>> retriever = LexicalRetriever([{"title": "Fed holds rates"}, {"title": "Election polls tighten"}])
    >>> retriever.search("fed rates", k=1)[0]["document"]["title"]
    'Fed holds rates'
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Any, Dict, List, Sequence

logger = logging.getLogger(__name__)

__all__ = ["LexicalRetriever"]

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    r"""Lowercase alphanumeric tokenisation."""
    return _TOKEN_PATTERN.findall(text.lower())


class LexicalRetriever:
    r"""BM25 lexical retriever over strings or dict documents.

    Args:
        documents: Documents to index (strings, or dicts with ``text_key``).
        text_key: Dict key holding the searchable text (default ``"title"``).
        k1: BM25 term-frequency saturation (default 1.5).
        b: BM25 length normalisation (default 0.75).
    """

    def __init__(
        self,
        documents: Sequence[Any],
        *,
        text_key: str = "title",
        k1: float = 1.5,
        b: float = 0.75,
    ):
        self.documents = list(documents)
        self.text_key = text_key
        self.k1 = k1
        self.b = b

        token_lists = [self._document_tokens(document) for document in self.documents]
        self._term_frequencies = [Counter(tokens) for tokens in token_lists]
        self._lengths = [max(1, len(tokens)) for tokens in token_lists]
        self._average_length = sum(self._lengths) / len(self._lengths) if self._lengths else 1.0

        document_frequency: Counter = Counter()
        for tokens in token_lists:
            for term in set(tokens):
                document_frequency[term] += 1
        total = len(self.documents) or 1
        self._idf = {
            term: math.log(1 + (total - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def _document_tokens(self, document: Any) -> List[str]:
        if isinstance(document, str):
            return _tokenize(document)
        if isinstance(document, dict):
            return _tokenize(str(document.get(self.text_key, "")))
        return _tokenize(str(document))

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        r"""Return the top-*k* documents for *query* with BM25 scores."""
        terms = _tokenize(query)
        if not terms or not self.documents:
            return []

        scored: List[tuple[float, int]] = []
        for index, frequencies in enumerate(self._term_frequencies):
            score = 0.0
            length_ratio = self._lengths[index] / self._average_length
            for term in terms:
                frequency = frequencies.get(term)
                if not frequency:
                    continue
                denominator = frequency + self.k1 * (1 - self.b + self.b * length_ratio)
                score += self._idf.get(term, 0.0) * (frequency * (self.k1 + 1)) / denominator
            if score > 0:
                scored.append((score, index))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {"score": round(score, 4), "document": self.documents[index]}
            for score, index in scored[: max(0, k)]
        ]
