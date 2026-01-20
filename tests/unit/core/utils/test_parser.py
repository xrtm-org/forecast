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

r"""Unit tests for forecast.core.utils.parser."""

import pytest

from forecast.core.utils.parser import parse_json_markdown


class TestParseJsonMarkdown:
    r"""Tests for the parse_json_markdown function."""

    def test_json_in_markdown_code_block(self):
        r"""Should extract JSON from markdown code blocks."""
        text = '''Here is the result:
```json
{"confidence": 0.8, "reasoning": "test"}
```
'''
        result = parse_json_markdown(text)
        assert result["confidence"] == 0.8
        assert result["reasoning"] == "test"

    def test_json_in_plain_code_block(self):
        r"""Should extract JSON from plain code blocks (no json specifier)."""
        text = '''
```
{"value": 42}
```
'''
        result = parse_json_markdown(text)
        assert result["value"] == 42

    def test_raw_json_dict(self):
        r"""Should parse raw JSON dict without markdown."""
        text = '{"key": "value"}'
        result = parse_json_markdown(text)
        assert result["key"] == "value"

    def test_raw_json_array(self):
        r"""Should parse raw JSON array without markdown."""
        text = '[1, 2, 3]'
        result = parse_json_markdown(text)
        assert result == [1, 2, 3]

    def test_json_with_preamble(self):
        r"""Should handle JSON with conversational preamble."""
        text = "Here is my analysis: {\"confidence\": 0.75}"
        result = parse_json_markdown(text)
        assert result["confidence"] == 0.75

    def test_json_with_postamble(self):
        r"""Should handle JSON with trailing text."""
        text = '{"answer": true} I hope this helps!'
        result = parse_json_markdown(text)
        assert result["answer"] is True

    def test_json_array_in_markdown(self):
        r"""Should extract JSON array from markdown."""
        text = '''Results:
```json
[{"id": 1}, {"id": 2}]
```
'''
        result = parse_json_markdown(text)
        assert len(result) == 2
        assert result[0]["id"] == 1

    def test_invalid_json_returns_default(self):
        r"""Should return default for invalid JSON."""
        text = "This is not JSON at all"
        result = parse_json_markdown(text, default={"error": True})
        assert result == {"error": True}

    def test_malformed_in_code_block_returns_default(self):
        r"""Should return default when code block contains invalid JSON and no valid JSON elsewhere."""
        text = '''
```json
{invalid json here}
```
No actual JSON here either
'''
        result = parse_json_markdown(text, default={"fallback": True})
        assert result == {"fallback": True}

    def test_nested_json(self):
        r"""Should handle nested JSON structures."""
        text = '{"outer": {"inner": {"deep": 42}}}'
        result = parse_json_markdown(text)
        assert result["outer"]["inner"]["deep"] == 42

    def test_empty_object(self):
        r"""Should handle empty JSON objects."""
        text = '{}'
        result = parse_json_markdown(text)
        assert result == {}

    def test_empty_array(self):
        r"""Should handle empty JSON arrays."""
        text = '[]'
        result = parse_json_markdown(text)
        assert result == []
