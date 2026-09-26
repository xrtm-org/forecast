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

r"""Tests for the model capability registry."""

from xrtm.forecast.core.config.models import ModelSpec, get_model_spec, register_model_spec


def test_deepseek_flash_known_capabilities():
    spec = get_model_spec("deepseek-flash")
    assert spec.provider == "deepseek"
    assert spec.supports_thinking is True
    assert spec.supports_json_mode is True
    assert spec.context_window == 1_048_576


def test_legacy_aliases_route_to_flash_spec():
    assert get_model_spec("deepseek-chat").model_id == "deepseek-flash"
    assert get_model_spec("deepseek-v4-flash").model_id == "deepseek-flash"


def test_unknown_model_is_conservative():
    spec = get_model_spec("some-future-model")
    assert spec.supports_thinking is False
    assert spec.supports_json_mode is False


def test_register_model_spec_overrides():
    register_model_spec(
        ModelSpec(
            model_id="custom-decision-model",
            provider="typesafe",
            supports_thinking=False,
            supports_json_mode=True,
        )
    )
    spec = get_model_spec("custom-decision-model")
    assert spec.provider == "typesafe"
    assert spec.supports_json_mode is True
