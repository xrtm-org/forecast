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

r"""Unit tests for forecast.core.utils.state_ops."""

from typing import Any, Dict, List

import pytest
from pydantic import BaseModel

from forecast.core.utils.state_ops import clone_state


class SimpleState(BaseModel):
    r"""Simple test state model."""

    name: str
    value: int
    tags: List[str] = []


class NestedState(BaseModel):
    r"""State with nested structure."""

    data: Dict[str, Any] = {}
    items: List[Dict[str, int]] = []


class TestCloneState:
    r"""Tests for the clone_state function."""

    def test_basic_clone(self):
        r"""Should create an independent copy of state."""
        original = SimpleState(name="test", value=42)
        cloned = clone_state(original)

        assert cloned.name == "test"
        assert cloned.value == 42
        assert cloned is not original

    def test_deep_copy_lists(self):
        r"""Should deep copy mutable lists."""
        original = SimpleState(name="test", value=1, tags=["a", "b"])
        cloned = clone_state(original)

        cloned.tags.append("c")

        assert original.tags == ["a", "b"]
        assert cloned.tags == ["a", "b", "c"]

    def test_deep_copy_dicts(self):
        r"""Should deep copy nested dicts."""
        original = NestedState(data={"key": "value"})
        cloned = clone_state(original)

        cloned.data["new_key"] = "new_value"

        assert "new_key" not in original.data
        assert cloned.data["new_key"] == "new_value"

    def test_overrides_simple_field(self):
        r"""Should apply simple field overrides."""
        original = SimpleState(name="old", value=1)
        cloned = clone_state(original, overrides={"name": "new"})

        assert original.name == "old"
        assert cloned.name == "new"

    def test_overrides_multiple_fields(self):
        r"""Should apply multiple overrides."""
        original = SimpleState(name="old", value=1)
        cloned = clone_state(original, overrides={"name": "new", "value": 99})

        assert cloned.name == "new"
        assert cloned.value == 99

    def test_overrides_invalid_key_raises(self):
        r"""Should raise ValueError for unknown override keys."""
        original = SimpleState(name="test", value=1)

        with pytest.raises(ValueError, match="Cannot override unknown state field"):
            clone_state(original, overrides={"nonexistent": "value"})

    def test_no_overrides(self):
        r"""Should work with None overrides."""
        original = SimpleState(name="test", value=42)
        cloned = clone_state(original, overrides=None)

        assert cloned.name == "test"
        assert cloned.value == 42

    def test_empty_overrides(self):
        r"""Should work with empty overrides dict."""
        original = SimpleState(name="test", value=42)
        cloned = clone_state(original, overrides={})

        assert cloned.name == "test"
        assert cloned.value == 42
