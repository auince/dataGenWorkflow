"""Type definitions for the LangGraph pipeline."""

from typing import TypedDict, List, Optional


class AnnotationResult(TypedDict):
    """Result of an image annotation."""

    image_path: str
    annotations: dict
    quality_score: Optional[float] = None
    error: Optional[str] = None


class CheckpointMetadata(TypedDict):
    """Metadata for graph checkpointing."""

    step: int
    timestamp: str
    agent_name: Optional[str] = None
