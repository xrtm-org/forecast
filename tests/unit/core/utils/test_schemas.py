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

r"""Tests for structured-output schema helpers."""

from pydantic import BaseModel

from xrtm.forecast.core.utils.schemas import (
    json_object_response_format,
    json_schema_response_format,
    to_json_schema,
)


class DemoModel(BaseModel):
    probability: float


def test_json_object_response_format():
    assert json_object_response_format() == {"type": "json_object"}


def test_to_json_schema_contains_properties():
    schema = to_json_schema(DemoModel)
    assert schema["properties"]["probability"]["type"] == "number"


def test_json_schema_response_format_shape():
    fmt = json_schema_response_format(DemoModel, name="demo", strict=True)
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["name"] == "demo"
    assert fmt["json_schema"]["strict"] is True
    assert "properties" in fmt["json_schema"]["schema"]
