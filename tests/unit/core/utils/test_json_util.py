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

r"""Unit tests for forecast.core.utils.json_util."""

from pydantic import BaseModel

from forecast.core.utils.json_util import robust_clean, safe_json_dumps


class TestRobustClean:
    r"""Tests for the robust_clean function."""

    def test_none_passthrough(self):
        r"""None should pass through unchanged."""
        assert robust_clean(None) is None

    def test_primitive_passthrough(self):
        r"""Primitives should pass through unchanged."""
        assert robust_clean("hello") == "hello"
        assert robust_clean(42) == 42
        assert robust_clean(True) is True
        assert robust_clean(3.14) == 3.14

    def test_nan_to_none(self):
        r"""NaN should be converted to None."""
        assert robust_clean(float("nan")) is None

    def test_inf_to_none(self):
        r"""Inf should be converted to None."""
        assert robust_clean(float("inf")) is None
        assert robust_clean(float("-inf")) is None

    def test_dict_cleaned(self):
        r"""Dicts should be recursively cleaned."""
        result = robust_clean({"a": 1, "b": float("nan"), "_private": "secret"})
        assert result == {"a": 1, "b": None}
        assert "_private" not in result

    def test_list_cleaned(self):
        r"""Lists should be recursively cleaned."""
        result = robust_clean([1, float("nan"), "hello"])
        assert result == [1, None, "hello"]

    def test_nested_structure(self):
        r"""Nested structures should be recursively cleaned."""
        data = {"items": [{"value": float("inf")}, {"value": 10}]}
        result = robust_clean(data)
        assert result == {"items": [{"value": None}, {"value": 10}]}

    def test_pydantic_v2_model(self):
        r"""Pydantic v2 models should be converted via model_dump."""

        class TestModel(BaseModel):
            name: str
            value: float

        model = TestModel(name="test", value=42.0)
        result = robust_clean(model)
        assert result == {"name": "test", "value": 42.0}

    def test_non_serializable_to_string(self):
        r"""Non-serializable objects should be converted to string."""

        class CustomObject:
            def __str__(self):
                return "custom_repr"

        result = robust_clean(CustomObject())
        assert result == "custom_repr"


class TestSafeJsonDumps:
    r"""Tests for the safe_json_dumps function."""

    def test_simple_object(self):
        r"""Simple objects should serialize correctly."""
        result = safe_json_dumps({"key": "value"})
        assert result == '{"key": "value"}'

    def test_with_nan(self):
        r"""Objects with NaN should serialize with null."""
        result = safe_json_dumps({"value": float("nan")})
        assert result == '{"value": null}'

    def test_with_kwargs(self):
        r"""Should pass kwargs to json.dumps."""
        result = safe_json_dumps({"a": 1}, indent=2)
        assert '"a": 1' in result
        assert "\n" in result
