from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class BaseGraphState(BaseModel):
    """
    Standardized state object tracking the reasoning lifecycle.
    Domain-agnostic and extensible.
    """

    subject_id: str = Field(description="The unique identifier for the subject being analyzed.")

    # Generic bucket for node outputs to avoid hardcoded domain fields
    node_reports: Dict[str, Any] = Field(default_factory=dict)

    # Feedback & Loop Control
    past_critique: str = ""
    cycle_count: int = 0
    max_cycles: int = 3

    # Operational Context
    context: Dict[str, Any] = Field(default_factory=dict)

    # Performance & Diagnostics
    latencies: Dict[str, float] = Field(default_factory=dict)
    usage: Dict[str, int] = Field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )

    # Communication & Audit
    execution_path: List[str] = Field(default_factory=list, description="Ordered list of agent names executed.")

    model_config = ConfigDict(arbitrary_types_allowed=True)
