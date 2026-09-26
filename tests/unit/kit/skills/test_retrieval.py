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

r"""Tests for the BM25 lexical retriever."""

from xrtm.forecast.kit.skills.retrieval import LexicalRetriever


def test_ranks_matching_document_first():
    retriever = LexicalRetriever(
        [
            {"title": "Fed holds interest rates steady"},
            {"title": "Election polls tighten in swing states"},
            {"title": "Fed signals rate cuts later this year"},
        ]
    )
    results = retriever.search("fed rate cuts", k=2)
    assert results[0]["document"]["title"] == "Fed signals rate cuts later this year"
    assert results[0]["score"] > 0


def test_supports_plain_strings():
    retriever = LexicalRetriever(["inflation cools", "storm warning issued"])
    results = retriever.search("inflation", k=1)
    assert results[0]["document"] == "inflation cools"


def test_empty_query_or_corpus_returns_empty():
    assert LexicalRetriever([]).search("anything") == []
    assert LexicalRetriever(["doc"]).search("") == []


def test_k_limits_results():
    retriever = LexicalRetriever(["a b c", "a b", "a"])
    assert len(retriever.search("a", k=2)) == 2
