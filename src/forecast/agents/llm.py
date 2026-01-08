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

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

from forecast.agents.base import Agent
from forecast.inference.base import InferenceProvider
from forecast.tools.registry import tool_registry
from forecast.utils.parser import parse_json_markdown

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMAgent(Agent):
    r"""
    An Agent that leverages a Large Language Model (LLM) for reasoning and task execution.

    `LLMAgent` provides common utilities for interacting with inference providers,
    retrieving tools from the registry, and parsing unstructured LLM output into
    structured Pydantic models.

    Args:
        model (`InferenceProvider`):
            The provider used to perform LLM inference (e.g., Gemini, OpenAI).
        name (`str`, *optional*):
            The logical name of the agent. Defaults to the class name.
    """

    def __init__(self, model: InferenceProvider, name: Optional[str] = None):
        super().__init__(name)
        self.model = model

    def get_tools(self, tool_names: Optional[List[str]] = None) -> List[Any]:
        r"""
        Retrieves tool instances from the global registry for LLM consumption.

        Args:
            tool_names (`List[str]`, *optional*):
                The names of specific tools to retrieve. If `None`, all registered
                tools are returned.

        Returns:
            `List[Any]`: A list of tool instances compatible with the agent's logic.
        """
        if tool_names is None:
            # Return all wrapped tool objects
            return [tool_registry.get_tool(name) for name in tool_registry.list_tools()]

        tools = []
        for name in tool_names:
            tool = tool_registry.get_tool(name)
            if tool:
                tools.append(tool)
        return tools

    def parse_output(
        self, text: str, schema: Optional[Type[T]] = None, default: Any = None
    ) -> Union[T, Dict[str, Any]]:
        r"""
        Parses raw text from an LLM response into a structured format.

        This utility handles JSON extraction from markdown blocks and optional
        validation against a Pydantic schema.

        Args:
            text (`str`):
                The raw response text from the LLM.
            schema (`Type[T]`, *optional*):
                The Pydantic model class to validate the output against.
            default (`Any`, *optional*):
                The value to return if parsing fails.

        Returns:
            `Union[T, Dict[str, Any]]`: The parsed model instance or dictionary.

        Example:
            ```python
            >>> from pydantic import BaseModel
            >>> class User(BaseModel): name: str
            >>> agent = LLMAgent(model=my_model)
            >>> user = agent.parse_output('{"name": "Alice"}', schema=User)
            >>> print(user.name)
            'Alice'
            ```
        """
        parsed = parse_json_markdown(text)
        if parsed is None:
            return default if default is not None else {}

        if schema and isinstance(parsed, dict):
            try:
                # Filter out keys not in schema to prevent validation errors
                valid_fields = schema.model_fields.keys()
                filtered = {k: v for k, v in parsed.items() if k in valid_fields}
                return schema(**filtered)
            except Exception as e:
                logger.warning(f"Schema validation failed: {e}")
                return default if default is not None else parsed
        return parsed

    async def run(self, input_data: Any, **kwargs) -> Any:
        r"""
        Primary execution loop for the LLM agent.

        Note:
            Base `LLMAgent` does not implement specific prompting logic.
            Subclasses must implement this method to define their persona and workflow.
        """
        raise NotImplementedError("LLMAgent subclasses must implement run")


__all__ = ["LLMAgent"]
