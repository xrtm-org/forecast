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

import xrtm.forecast as forecast
import xrtm.forecast.kit as kit
from xrtm.forecast.kit.agents.llm import LLMAgent
from xrtm.forecast.providers.inference.factory import ModelFactory


def test_top_level_all_is_curated() -> None:
    assert "Orchestrator" in forecast.__all__
    assert "create_forecasting_analyst" in forecast.__all__
    assert "LLMAgent" not in forecast.__all__
    assert "ModelFactory" not in forecast.__all__


def test_top_level_legacy_aliases_remain_available() -> None:
    from xrtm.forecast import LLMAgent as imported_llm_agent
    from xrtm.forecast import ModelFactory as imported_model_factory

    assert imported_llm_agent is LLMAgent
    assert imported_model_factory is ModelFactory


def test_kit_root_prefers_namespaces_but_keeps_legacy_aliases() -> None:
    from xrtm.forecast.kit import agents

    assert "agents" in kit.__all__
    assert agents.LLMAgent is LLMAgent
