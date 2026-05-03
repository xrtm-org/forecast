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

r"""Stable public entrypoint for xrtm-forecast.

Prefer importing specialist agents, providers, tools, and other advanced
components from their dedicated subpackages. The top-level package keeps a
small stable surface while preserving legacy convenience imports for
compatibility.
"""

from importlib import import_module
from typing import Any

from xrtm.forecast.core.orchestrator import Orchestrator
from xrtm.forecast.core.runtime import AsyncRuntime
from xrtm.forecast.core.schemas.graph import BaseGraphState, TemporalContext
from xrtm.forecast.kit.assistants.main import create_forecasting_analyst, create_local_analyst
from xrtm.forecast.version import __author__, __contact__, __copyright__, __license__, __version__

_LEGACY_EXPORTS: dict[str, tuple[str, str]] = {
    "Agent": ("xrtm.forecast.kit.agents.base", "Agent"),
    "ForecastingAnalyst": ("xrtm.forecast.kit.agents.specialists.analyst", "ForecastingAnalyst"),
    "registry": ("xrtm.forecast.kit.agents.registry", "registry"),
    "LLMAgent": ("xrtm.forecast.kit.agents.llm", "LLMAgent"),
    "ToolAgent": ("xrtm.forecast.kit.agents.tool", "ToolAgent"),
    "GraphAgent": ("xrtm.forecast.kit.agents.graph", "GraphAgent"),
    "RoutingAgent": ("xrtm.forecast.kit.agents.routing", "RoutingAgent"),
    "ModelFactory": ("xrtm.forecast.providers.inference.factory", "ModelFactory"),
    "Memory": ("xrtm.forecast.kit.memory.unified", "Memory"),
    "auditor": ("xrtm.forecast.core.telemetry.audit", "auditor"),
    "tool_registry": ("xrtm.forecast.providers.tools", "tool_registry"),
    "SQLSkill": ("xrtm.forecast.providers.tools", "SQLSkill"),
    "PandasSkill": ("xrtm.forecast.providers.tools", "PandasSkill"),
}

__all__ = [
    "Orchestrator",
    "AsyncRuntime",
    "BaseGraphState",
    "TemporalContext",
    "create_forecasting_analyst",
    "create_local_analyst",
    "__version__",
    "__author__",
    "__contact__",
    "__license__",
    "__copyright__",
]


def __getattr__(name: str) -> Any:
    if name not in _LEGACY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _LEGACY_EXPORTS[name]
    return getattr(import_module(module_name), attr_name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LEGACY_EXPORTS))
