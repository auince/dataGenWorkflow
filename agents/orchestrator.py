"""DataOrchestrator - Main coordinator for multi-agent data generation pipeline."""

import asyncio
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime

from agents.base import BaseAgent
from agents.ingestion import IngestionAgent, IngestionState
from agents.annotation import AnnotationAgent, AnnotationState
from agents.text_generation import TextGenAgent
from agents.refinement import RefinementAgent, RefinementState
from agents.validation import ValidationAgent, ValidationState
from agents.distillation import DistillationAgent, DistillationState
from utils.logger import get_logger

from graph.state import PipelineState
from graph.types import AnnotationResult


class DataOrchestratorState(TypedDict):
    """Unified state for the entire data generation pipeline."""

    image_dir: str
    images: List[Dict[str, Any]]
    total_found: int
    duplicates_removed: int
    low_quality_removed: int
    errors: List[str]
    current_image: str
    annotations: dict
    masks: list
    small_target_masks: list
    refined_masks: List[Dict[str, Any]]
    quality_score: Optional[float]
    evaluation_result: str
    evaluation_details: Dict[str, Any]
    validation_passed: bool
    validation_errors: List[str]
    distilled_samples: List[Dict[str, Any]]
    distillation_metrics: Dict[str, float]
    generated_prompts: List[str]
    total_images: int
    processed_count: int
    failed_count: int
    iteration_round: int
    completed_annotations: List[AnnotationResult]


class DataOrchestrator:
    """Main coordinator that integrates all agents for the data generation pipeline.

    Manages DAG workflow and agent-to-agent data passing.

    Pipeline flow:
        Ingestion -> Annotation -> Refinement -> Validation -> Distillation
                                                       |
                                                       v
                                              TextGenAgent (parallel)

    Each agent processes the unified state and passes results to the next agent.
    """

    def __init__(
        self,
        image_dir: str,
        min_width: int = 256,
        min_height: int = 256,
        min_quality: int = 30,
        model_path: str = "/data/lch/SAM/ultralytics-main/sam3.pt",
        device: Optional[str] = None,
    ):
        """Initialize DataOrchestrator.

        Args:
            image_dir: Directory containing input images
            min_width: Minimum image width for quality check
            min_height: Minimum image height for quality check
            min_quality: Minimum quality score for images
            model_path: Path to SAM3 model checkpoint
            device: Computation device (cuda/cpu), auto-detected if None
        """
        self.logger = get_logger("DataOrchestrator")

        self.ingestion_agent = IngestionAgent(
            name="ingestion",
            min_width=min_width,
            min_height=min_height,
            min_quality=min_quality,
        )

        self.annotation_agent = AnnotationAgent(
            name="annotation_agent",
            model_path=model_path,
            device=device,
        )

        self.refinement_agent = RefinementAgent(name="refinement")
        self.validation_agent = ValidationAgent(name="validation")
        self.distillation_agent = DistillationAgent(name="distillation")
        self.textgen_agent = TextGenAgent(name="text_generator")

        self.dag = {
            "ingestion": "annotation",
            "annotation": "refinement",
            "refinement": "validation",
            "validation": "distillation",
            "distillation": "complete",
            "textgen": "complete",
        }

        self.state: DataOrchestratorState = {
            "image_dir": image_dir,
            "images": [],
            "total_found": 0,
            "duplicates_removed": 0,
            "low_quality_removed": 0,
            "errors": [],
            "current_image": "",
            "annotations": {},
            "masks": [],
            "small_target_masks": [],
            "refined_masks": [],
            "quality_score": None,
            "evaluation_result": "pass",
            "evaluation_details": {},
            "validation_passed": False,
            "validation_errors": [],
            "distilled_samples": [],
            "distillation_metrics": {},
            "generated_prompts": [],
            "total_images": 0,
            "processed_count": 0,
            "failed_count": 0,
            "iteration_round": 0,
            "completed_annotations": [],
        }

        self.logger.info("DataOrchestrator initialized")

    def _convert_to_ingestion_state(
        self, state: DataOrchestratorState
    ) -> IngestionState:
        """Convert unified state to IngestionState."""
        return {
            "image_dir": state["image_dir"],
            "images": state["images"],
            "total_found": state["total_found"],
            "duplicates_removed": state["duplicates_removed"],
            "low_quality_removed": state["low_quality_removed"],
            "errors": state["errors"],
        }

    def _convert_to_annotation_state(
        self, state: DataOrchestratorState
    ) -> AnnotationState:
        """Convert unified state to AnnotationState."""
        return {
            "current_image": state["current_image"],
            "annotations": state["annotations"],
            "masks": state["masks"],
            "small_target_masks": state["small_target_masks"],
        }

    def _convert_to_refinement_state(
        self, state: DataOrchestratorState
    ) -> RefinementState:
        """Convert unified state to RefinementState."""
        annotations = state.get("annotations", {})
        image_size = (
            annotations.get("image_height", 0),
            annotations.get("image_width", 0),
        )
        return {
            "masks": state["masks"],
            "image_size": image_size,
            "refined_masks": state["refined_masks"],
        }

    def _convert_to_validation_state(
        self, state: DataOrchestratorState
    ) -> ValidationState:
        """Convert unified state to ValidationState."""
        return {
            "current_image": state.get("current_image", ""),
            "masks": state.get("masks", []),
            "annotations": state.get("annotations", {}),
            "quality_score": state.get("quality_score"),
            "evaluation_result": state.get("evaluation_result", "pass"),
            "evaluation_details": state.get("evaluation_details", {}),
        }

    def _convert_to_distillation_state(
        self, state: DataOrchestratorState
    ) -> DistillationState:
        """Convert unified state to DistillationState."""
        return {
            "refined_masks": state["refined_masks"],
            "distilled_samples": state["distilled_samples"],
            "distillation_metrics": state["distillation_metrics"],
        }

    def _update_state_from_ingestion(
        self, source: IngestionState, target: DataOrchestratorState
    ):
        """Update unified state from IngestionState."""
        target["images"] = source["images"]
        target["total_found"] = source["total_found"]
        target["duplicates_removed"] = source["duplicates_removed"]
        target["low_quality_removed"] = source["low_quality_removed"]
        target["errors"] = source["errors"]
        target["total_images"] = len(source["images"])

    def _update_state_from_annotation(
        self, source: AnnotationState, target: DataOrchestratorState
    ):
        """Update unified state from AnnotationState."""
        target["current_image"] = source["current_image"]
        target["annotations"] = source["annotations"]
        target["masks"] = source["masks"]
        target["small_target_masks"] = source["small_target_masks"]

    def _update_state_from_refinement(
        self, source: RefinementState, target: DataOrchestratorState
    ):
        """Update unified state from RefinementState."""
        target["refined_masks"] = source["refined_masks"]

    def _update_state_from_validation(
        self, source: ValidationState, target: DataOrchestratorState
    ):
        """Update unified state from ValidationState."""
        target["quality_score"] = source.get("quality_score")
        target["evaluation_result"] = source.get("evaluation_result", "pass")
        target["evaluation_details"] = source.get("evaluation_details", {})
        # Also keep legacy fields for backward compatibility
        target["validation_passed"] = source.get("evaluation_result") == "pass"
        target["validation_errors"] = source.get("evaluation_details", {}).get(
            "errors", []
        )

    def _update_state_from_distillation(
        self, source: DistillationState, target: DataOrchestratorState
    ):
        """Update unified state from DistillationState."""
        target["distilled_samples"] = source["distilled_samples"]
        target["distillation_metrics"] = source["distillation_metrics"]

    async def _run_ingestion(self) -> DataOrchestratorState:
        """Run ingestion agent."""
        self.logger.info("Running ingestion agent")
        ingestion_state = self._convert_to_ingestion_state(self.state)
        result = await self.ingestion_agent.process(ingestion_state)
        self._update_state_from_ingestion(result, self.state)
        return self.state

    async def _run_annotation(self, image_path: str) -> DataOrchestratorState:
        """Run annotation agent for a single image."""
        self.logger.info(f"Running annotation agent for: {image_path}")
        self.state["current_image"] = image_path
        annotation_state = self._convert_to_annotation_state(self.state)
        result = await self.annotation_agent.process(annotation_state)
        self._update_state_from_annotation(result, self.state)
        return self.state

    async def _run_refinement(self) -> DataOrchestratorState:
        """Run refinement agent."""
        self.logger.info("Running refinement agent")
        refinement_state = self._convert_to_refinement_state(self.state)
        result = await self.refinement_agent.process(refinement_state)
        self._update_state_from_refinement(result, self.state)
        return self.state

    async def _run_validation(self) -> DataOrchestratorState:
        """Run validation agent."""
        self.logger.info("Running validation agent")
        validation_state = self._convert_to_validation_state(self.state)
        result = await self.validation_agent.process(validation_state)
        self._update_state_from_validation(result, self.state)
        return self.state

    async def _run_distillation(self) -> DataOrchestratorState:
        """Run distillation agent."""
        self.logger.info("Running distillation agent")
        distillation_state = self._convert_to_distillation_state(self.state)
        result = await self.distillation_agent.process(distillation_state)
        self._update_state_from_distillation(result, self.state)
        return self.state

    async def _run_textgen(self) -> DataOrchestratorState:
        """Run text generation agent."""
        self.logger.info("Running text generation agent")
        pipeline_state: PipelineState = {
            "total_images": self.state["total_images"],
            "processed_count": self.state["processed_count"],
            "failed_count": self.state["failed_count"],
            "current_image": self.state["current_image"],
            "current_image_results": [],
            "iteration_round": self.state["iteration_round"],
            "low_quality_samples": [],
            "completed_annotations": self.state["completed_annotations"],
            "discarded_samples": [],
            "checkpoint": {"step": 0, "timestamp": datetime.now().isoformat()},
        }
        result = await self.textgen_agent.process(pipeline_state)
        self.state["generated_prompts"] = result.get("generated_prompts", [])
        return self.state

    async def _process_single_image(self, image_path: str) -> bool:
        """Process a single image through the pipeline.

        Args:
            image_path: Path to image file

        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            await self._run_annotation(image_path)
            await self._run_refinement()
            await self._run_validation()

            if self.state.get("evaluation_result") != "pass":
                self.logger.warning(
                    f"Validation failed for {image_path}: "
                    f"{self.state.get('evaluation_result')}"
                )
                self.state["failed_count"] += 1
                return False

            await self._run_distillation()

            annotation_result: AnnotationResult = {
                "image_path": image_path,
                "annotations": self.state["annotations"],
                "quality_score": self.state.get("quality_score") or 0.0,
            }
            self.state["completed_annotations"].append(annotation_result)
            self.state["processed_count"] += 1

            return True

        except Exception as e:
            self.logger.error(f"Error processing {image_path}: {e}")
            self.state["failed_count"] += 1
            self.state["errors"].append(f"{image_path}: {str(e)}")
            return False

    async def run(self) -> DataOrchestratorState:
        """Run the complete data generation pipeline.

        Pipeline stages:
        1. Ingestion - load and quality-check images
        2. For each image: Annotation -> Refinement -> Validation -> Distillation
        3. TextGen - generate prompts for completed annotations (can run parallel)

        Returns:
            Final pipeline state with all results
        """
        self.logger.info("Starting data generation pipeline")

        await self._run_ingestion()
        self.logger.info(
            f"Ingestion complete: {len(self.state['images'])} images ready"
        )

        if not self.state["images"]:
            self.logger.warning("No images found after ingestion")
            return self.state

        image_paths = [img["path"] for img in self.state["images"]]
        textgen_task = None

        for image_path in image_paths:
            success = await self._process_single_image(image_path)

            if success and textgen_task is None:
                textgen_task = asyncio.create_task(self._run_textgen())

        if textgen_task:
            await textgen_task

        self.logger.info(
            f"Pipeline complete: {self.state['processed_count']} succeeded, "
            f"{self.state['failed_count']} failed"
        )

        return self.state

    def get_results(self) -> Dict[str, Any]:
        """Get pipeline results summary.

        Returns:
            Dictionary with results summary
        """
        return {
            "total_images": self.state["total_images"],
            "processed_count": self.state["processed_count"],
            "failed_count": self.state["failed_count"],
            "completed_annotations": self.state["completed_annotations"],
            "distilled_samples": self.state["distilled_samples"],
            "distillation_metrics": self.state["distillation_metrics"],
            "generated_prompts": self.state["generated_prompts"],
            "errors": self.state["errors"],
        }

    def get_state(self) -> DataOrchestratorState:
        """Get the current pipeline state.

        Returns:
            Current DataOrchestratorState
        """
        return self.state
