"""Pipeline state definition for LangGraph multi-agent pipeline."""

from typing import TypedDict, Optional, List, Dict, Any

from .types import AnnotationResult, CheckpointMetadata


class PipelineState(TypedDict):
    """State schema for the multi-agent annotation pipeline.

    This is the unified state used throughout the LangGraph pipeline,
    containing fields from all agent states plus pipeline-level tracking.
    """

    total_images: int
    processed_count: int
    failed_count: int
    current_image: Optional[str]
    current_image_results: List[AnnotationResult]
    iteration_round: int
    low_quality_samples: List[str]
    completed_annotations: List[AnnotationResult]
    discarded_samples: List[str]
    checkpoint: CheckpointMetadata

    image_dir: str
    output_dir: str
    images: List[Dict[str, Any]]
    annotations: dict
    masks: list
    small_target_masks: list
    refined_masks: list
    text_prompts: List[str]
    validation_passed: bool
    validation_errors: List[str]
    distilled_samples: list
    distillation_metrics: Dict[str, float]
    generated_prompts: List[str]
    errors: List[str]
    quality_score: Optional[float]
    evaluation_result: str
    evaluation_details: Dict[str, Any]
