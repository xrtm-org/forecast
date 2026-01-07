from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MetadataBase(BaseModel):
    """
    Base class for metadata blocks to ensure consistency across schemas.
    """
    model_config = ConfigDict(extra="allow")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    market_type: Optional[str] = None
    source_version: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class ForecastQuestion(BaseModel):
    """
    Generic input for a forecasting task.
    Scales from a simple string to a complex market event.
    """
    id: str = Field(..., description="Unique identifier for the question")
    title: str = Field(..., description="The main question or content to forecast")
    content: Optional[str] = Field(None, description="Detailed context or prompt body")

    metadata: MetadataBase = Field(default_factory=MetadataBase)

class CausalNode(BaseModel):
    """
    A single node in a logical causal chain.
    """
    event: str = Field(..., description="The assumption or event in the chain")
    probability: Optional[float] = Field(None, ge=0, le=1)
    description: Optional[str] = None

class ForecastOutput(BaseModel):
    """
    The model's generated forecast with dual-trace causality.
    """
    question_id: str
    confidence: float = Field(..., ge=0, le=1, description="Probability of the primary outcome")
    reasoning: str = Field(..., description="Narrative reasoning for the forecast")

    # Causal Architecture
    logical_trace: List[CausalNode] = Field(
        default_factory=list,
        description="The Bayesian-style sequence of assumptions (Mental Model)"
    )
    structural_trace: List[str] = Field(
        default_factory=list,
        description="Order of graph nodes executed (Audit Trail)"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Model info, latency, usage, cost")

class ForecastResolution(BaseModel):
    """
    Ground truth result for a forecast question.
    """
    question_id: str
    outcome: str = Field(..., description="The final winning outcome or value")
    resolved_at: datetime = Field(default_factory=datetime.utcnow)

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source info, verification method")
