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

import json
import math
from typing import Any


def robust_clean(obj: Any) -> Any:
    """
    Recursively cleans objects for JSON serializability.
    Handles:
    - Pydantic models (v1 & v2)
    - NaNs and Infs (converts to None)
    - Non-serializable objects (converts to str)
    - Strips internal keys (starting with _)
    """
    if obj is None:
        return None

    # Handle Pydantic models
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    elif hasattr(obj, "dict"):
        obj = obj.dict()

    if isinstance(obj, dict):
        return {k: robust_clean(v) for k, v in obj.items() if not k.startswith("_")}
    elif isinstance(obj, list):
        return [robust_clean(x) for x in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (str, int, bool)):
        return obj
    else:
        # Fallback to string representation to avoid crash
        return str(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Combines robust_clean and json.dumps."""
    return json.dumps(robust_clean(obj), **kwargs)
