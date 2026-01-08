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

import inspect
from typing import Any, Callable, Optional

from forecast.agents.base import Agent


class ToolAgent(Agent):
    r"""
    A specialized Agent that wraps a deterministic Python function or Tool.

    `ToolAgent` allows any standalone function to be treated as a first-class agent
    within the xrtm-forecast ecosystem. This is useful for integrating existing
    utilities into a reasoning graph.

    Args:
        fn (`Callable`):
            The function or tool to be wrapped. Can be synchronous or asynchronous.
        name (`str`, *optional*):
            The logical name of the agent. Defaults to the function's `__name__`.
    """

    def __init__(self, fn: Callable, name: Optional[str] = None):
        super().__init__(name or fn.__name__)
        self.fn = fn

    async def run(self, input_data: Any, **kwargs) -> Any:
        r"""
        Executes the wrapped function with the provided input.

        This method automatically detects if the function is asynchronous and
        handles the dispatch accordingly. If `input_data` is a dictionary,
        it will be unpacked as keyword arguments.

        Args:
            input_data (`Any`):
                The data to pass to the function.
            **kwargs:
                Additional execution context (usually ignored by the wrapped function
                unless it explicitly accepts them).

        Returns:
            `Any`: The return value of the wrapped function.
        """
        # Handling for both async and sync functions
        if inspect.iscoroutinefunction(self.fn):
            if isinstance(input_data, dict):
                return await self.fn(**input_data)
            return await self.fn(input_data)
        else:
            if isinstance(input_data, dict):
                return self.fn(**input_data)
            return self.fn(input_data)


__all__ = ["ToolAgent"]
