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

r"""Tests for the search tools (DeepSeek in-house + skill provider selection)."""

import json

from xrtm.forecast.kit.skills.web_search import WebSearchSkill
from xrtm.forecast.kit.tools.search import DeepSeekSearchTool, TavilySearchTool


class _Response:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._payload


def test_deepseek_search_maps_summary_and_clamps_request(monkeypatch):
    captured = {}

    def _urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode())
        captured["auth"] = request.headers.get("Authorization")
        return _Response(
            {
                "results": [
                    {"title": "T1", "url": "https://x", "summary": "long summary", "snippet": "short"},
                    {"title": "", "url": "", "snippet": "only snippet"},
                ]
            }
        )

    monkeypatch.setattr("xrtm.forecast.kit.tools.search.urllib.request.urlopen", _urlopen)

    results = DeepSeekSearchTool(api_key="test-key", max_results=9).search("  " + "q" * 200 + "  ")

    assert captured["url"].endswith("/v1/tools/search")
    assert captured["body"]["query"] == "q" * 128
    assert captured["body"]["count"] == 9
    assert captured["body"]["need_content"] is False
    assert captured["auth"] == "Bearer test-key"
    assert results[0]["content"] == "long summary"  # summary preferred over snippet
    assert results[1]["title"] == "Untitled"
    assert results[1]["content"] == "only snippet"


def test_deepseek_search_retries_transient_errors(monkeypatch):
    import urllib.error

    calls = {"n": 0}

    def _urlopen(request, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(request.full_url, 429, "rate limited", {}, None)
        return _Response({"results": [{"title": "ok", "url": "https://x"}]})

    monkeypatch.setattr("xrtm.forecast.kit.tools.search.urllib.request.urlopen", _urlopen)
    monkeypatch.setattr("xrtm.forecast.kit.tools.search.time.sleep", lambda _seconds: None)

    assert DeepSeekSearchTool(api_key="k").search("q")[0]["title"] == "ok"
    assert calls["n"] == 2


def test_deepseek_search_does_not_retry_client_errors(monkeypatch):
    import urllib.error

    calls = {"n": 0}

    def _urlopen(request, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(request.full_url, 400, "bad query", {}, None)

    monkeypatch.setattr("xrtm.forecast.kit.tools.search.urllib.request.urlopen", _urlopen)

    assert DeepSeekSearchTool(api_key="k").search("q") == []
    assert calls["n"] == 1


def test_deepseek_search_without_key_is_a_noop():
    assert DeepSeekSearchTool(api_key="").search("q") == []


def test_web_search_skill_picks_a_provider_from_the_environment(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("TVLY_DEV_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")

    assert isinstance(WebSearchSkill()._search_tool, DeepSeekSearchTool)

    monkeypatch.setenv("TAVILY_API_KEY", "tavily-key")
    assert isinstance(WebSearchSkill()._search_tool, TavilySearchTool)
