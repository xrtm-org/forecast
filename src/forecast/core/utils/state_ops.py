from typing import Any, Dict, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def clone_state(state: T, overrides: Dict[str, Any] | None = None) -> T:
    """
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
    """
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
