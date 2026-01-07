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
