from typing import Any, Dict, List

import pytest
from pydantic import BaseModel

from forecast.core.utils.state_ops import clone_state


class MockState(BaseModel):
    count: int
    tags: List[str]
    metadata: Dict[str, Any]


def test_clone_state_deep_copy():
    """Verify that mutable fields are truly deep copied."""
    initial = MockState(count=1, tags=["a", "b"], metadata={"x": 1})

    # Create clone
    clone = clone_state(initial)

    # Modify clone
    clone.count = 2
    clone.tags.append("c")
    clone.metadata["y"] = 2

    # Assert initial is untouched
    assert initial.count == 1
    assert initial.tags == ["a", "b"]
    assert "y" not in initial.metadata

    # Assert clone is modified
    assert clone.count == 2
    assert clone.tags == ["a", "b", "c"]
    assert clone.metadata["x"] == 1
    assert clone.metadata["y"] == 2


def test_clone_state_overrides():
    """Verify that overrides are applied correctly."""
    initial = MockState(count=1, tags=["a"], metadata={})

    # Clone with overrides
    overrides = {"count": 99, "tags": ["z"]}
    clone = clone_state(initial, overrides=overrides)

    assert clone.count == 99
    assert clone.tags == ["z"]
    # Unchanged field remains
    assert clone.metadata == {}

    # Initial untouched
    assert initial.count == 1


def test_clone_state_invalid_override():
    """Verify error on unknown field."""
    initial = MockState(count=1, tags=[], metadata={})

    with pytest.raises(ValueError, match="Cannot override unknown state field: 'bad_key'"):
        clone_state(initial, overrides={"bad_key": 123})
