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

from typing import Any, Dict, Optional

from forecast.core.schemas.graph import TemporalContext
from forecast.core.tools.base import Tool


class GuardianTool(Tool):
    r"""
    A specific wrapper that enforces Temporal Integrity on any tool.

    If the system is running in a `strict_mode` backtest, the GuardianTool
    will block execution of any tool that does not explicitly declare
    `pit_supported=True`.

    This prevents accidental data leakage where an agent uses a generic
    search tool (like Google) to find answers from the future.
    """

    def __init__(self, tool: Tool):
        self._tool = tool

    @property
    def name(self) -> str:
        return self._tool.name

    @property
    def description(self) -> str:
        return f"[GUARDIAN WRAPPED] {self._tool.description}"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return self._tool.parameters_schema

    @property
    def pit_supported(self) -> bool:
        r"""
        The wrapper itself supports PiT because its *job* is to enforce it.
        However, it delegates the actual check to the wrapped tool's property.
        """
        return True

    async def run(self, temporal_context: Optional[TemporalContext] = None, **kwargs: Any) -> Any:
        r"""
        Executes the wrapped tool with strict temporal validation.

        Raises:
            RuntimeError: If strict mode is active and the tool is not PiT-safe.
        """
        if temporal_context and temporal_context.is_backtest and temporal_context.strict_mode:
            if not self._tool.pit_supported:
                raise RuntimeError(
                    f"TEMPORAL VIOLATION: Tool '{self.name}' is not Point-in-Time (PiT) safe. "
                    f"Execution blocked by Guardian protocol for date {temporal_context.today_str}."
                )

        # Proceed with execution
        return await self._tool.run(temporal_context=temporal_context, **kwargs)


__all__ = ["GuardianTool"]
