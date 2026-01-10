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

from typing import Any, Dict, TypeVar

from pydantic import BaseModel

__all__ = ["clone_state"]


T = TypeVar("T", bound=BaseModel)


def clone_state(state: T, overrides: Dict[str, Any] | None = None) -> T:
    r"""
    Creates a deep copy of a Pydantic state model and applies overrides.

    This ensures that branches are fully isolated from each other. Modifications
    in one branch (e.g., appending to a list in the state) will not affect
    others.

    Args:
        state: The base state object (must be a Pydantic model).
        overrides: A dictionary of field names and values to overwrite in the copy.

    Returns:
        A new instance of the state class with the copied/overridden data.

    Raises:
        ValueError: If overrides contains keys that are not in the state model.
    r"""
    # 1. Deep copy the model to ensure mutable containers (lists, dicts) are distinct
    new_state = state.model_copy(deep=True)

    # 2. Apply overrides if provided
    if overrides:
        # Validate keys first
        valid_keys = (
            new_state.model_fields.keys()
            if hasattr(new_state, "model_fields")
            else new_state.__class__.model_fields.keys()
        )

        # Pydantic v2 prefer accessing via class or checking dict
        # Actually better to just use getattr/setattr and let pydantic validate type if we wanted,
        # but here we just want to ensure the key exists.

        # Best practice for V2 instance:
        # valid_keys = new_state.__class__.model_fields.keys()
        for key, value in overrides.items():
            if key not in valid_keys:
                raise ValueError(f"Cannot override unknown state field: '{key}'")

            # We use setattr for Pydantic models
            setattr(new_state, key, value)

    return new_state
