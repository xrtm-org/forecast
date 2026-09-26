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

r"""Structured-output schema helpers.

Bridges Pydantic models to OpenAI-compatible ``response_format`` payloads so
agents can request provider-enforced JSON instead of relying on prompt-only
schema instructions.

Example:
    >>> from pydantic import BaseModel
    >>> from xrtm.forecast.core.utils.schemas import json_object_response_format
    >>> json_object_response_format()
    {'type': 'json_object'}
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

__all__ = [
    "to_json_schema",
    "json_object_response_format",
    "json_schema_response_format",
]


def to_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    r"""Return the JSON schema for a Pydantic model.

    Args:
        model: A Pydantic model class.

    Returns:
        The model's JSON schema as a dictionary.
    """
    return model.model_json_schema()


def json_object_response_format() -> Dict[str, Any]:
    r"""Return the OpenAI-compatible ``json_object`` response format.

    This is the broadly supported structured-output mode (OpenAI, DeepSeek).
    The prompt must still mention JSON so the model knows what to produce.
    """
    return {"type": "json_object"}


def json_schema_response_format(
    model: Type[BaseModel],
    name: Optional[str] = None,
    strict: bool = False,
) -> Dict[str, Any]:
    r"""Return the OpenAI-compatible ``json_schema`` response format for a model.

    Provider support varies; prefer :func:`json_object_response_format` when in
    doubt and fall back to prompt-level schema instructions.

    Args:
        model: Pydantic model class describing the expected response.
        name: Schema name reported to the provider (defaults to the class name).
        strict: Whether to request strict schema adherence.

    Returns:
        A ``response_format`` dictionary ready to pass to a chat completion.
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name or model.__name__,
            "schema": to_json_schema(model),
            "strict": strict,
        },
    }
