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

r"""Namespace entrypoint for higher-level forecasting building blocks.

Prefer importing concrete agents, topologies, and sentinels from their
subpackages. The kit root intentionally favors namespaces over becoming a
catch-all surface.
"""

from importlib import import_module
from typing import Any

from xrtm.forecast.kit.workbench import AnalystWorkbench

_NAMESPACE_EXPORTS: dict[str, str] = {
    "agents": "xrtm.forecast.kit.agents",
    "memory": "xrtm.forecast.kit.memory",
    "pipelines": "xrtm.forecast.kit.pipelines",
    "sentinel": "xrtm.forecast.kit.sentinel",
    "skills": "xrtm.forecast.kit.skills",
    "stages": "xrtm.forecast.kit.stages",
    "topologies": "xrtm.forecast.kit.topologies",
}

_LEGACY_EXPORTS: dict[str, tuple[str, str]] = {
    "RecursiveConsensus": ("xrtm.forecast.kit.topologies", "RecursiveConsensus"),
    "create_ivw_aggregator": ("xrtm.forecast.kit.topologies", "create_ivw_aggregator"),
    "create_simple_aggregator": ("xrtm.forecast.kit.topologies", "create_simple_aggregator"),
    "RedTeamAgent": ("xrtm.forecast.kit.agents.red_team", "RedTeamAgent"),
    "FactCheckerAgent": ("xrtm.forecast.kit.agents.fact_checker", "FactCheckerAgent"),
    "PollingDriver": ("xrtm.forecast.kit.sentinel", "PollingDriver"),
    "SentinelDriver": ("xrtm.forecast.kit.sentinel", "SentinelDriver"),
    "TriggerRules": ("xrtm.forecast.kit.sentinel", "TriggerRules"),
}

__all__ = [*_NAMESPACE_EXPORTS, "AnalystWorkbench"]


def __getattr__(name: str) -> Any:
    if name in _NAMESPACE_EXPORTS:
        return import_module(_NAMESPACE_EXPORTS[name])
    if name in _LEGACY_EXPORTS:
        module_name, attr_name = _LEGACY_EXPORTS[name]
        return getattr(import_module(module_name), attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_NAMESPACE_EXPORTS) | set(_LEGACY_EXPORTS))
