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

Prefer importing concrete agents, topologies, and skills from their
subpackages. The kit root intentionally favors namespaces over becoming a
catch-all surface.
"""

from importlib import import_module
from typing import Any

_NAMESPACE_EXPORTS: dict[str, str] = {
    "agents": "xrtm.forecast.kit.agents",
    "skills": "xrtm.forecast.kit.skills",
    "topologies": "xrtm.forecast.kit.topologies",
}

_LEGACY_EXPORTS: dict[str, tuple[str, str]] = {
    "RecursiveConsensus": ("xrtm.forecast.kit.topologies", "RecursiveConsensus"),
    "create_ivw_aggregator": ("xrtm.forecast.kit.topologies", "create_ivw_aggregator"),
    "create_simple_aggregator": ("xrtm.forecast.kit.topologies", "create_simple_aggregator"),
}

__all__ = [*_NAMESPACE_EXPORTS]


def __getattr__(name: str) -> Any:
    if name in _NAMESPACE_EXPORTS:
        return import_module(_NAMESPACE_EXPORTS[name])
    if name in _LEGACY_EXPORTS:
        module_name, attr_name = _LEGACY_EXPORTS[name]
        return getattr(import_module(module_name), attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_NAMESPACE_EXPORTS) | set(_LEGACY_EXPORTS))
