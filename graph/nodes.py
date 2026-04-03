"""DAG node functions for the multi-agent annotation pipeline."""

import asyncio
from typing import TypedDict
from datetime import datetime

from agents.ingestion import IngestionAgent, IngestionState, QualityCheckTool
from agents.annotation import AnnotationAgent, AnnotationState
from agents.prompt_gen import PromptGenAgent, PromptGenState
from agents.refinement import RefinementAgent, RefinementState
from agents.distillation import DistillationAgent, DistillationState
from agents.validation import ValidationAgent, ValidationState
from graph.state import PipelineState
from utils.logger import get_logger


_ingestion_agent: IngestionAgent | None = None
_annotation_agent: AnnotationAgent | None = None
_promptgen_agent: PromptGenAgent | None = None
_refinement_agent: RefinementAgent | None = None
_distillation_agent: DistillationAgent | None = None


def _get_ingestion_agent() -> IngestionAgent:
    global _ingestion_agent
    if _ingestion_agent is None:
        _ingestion_agent = IngestionAgent(
            name="ingestion", skip_deduplication=True, skip_quality_check=True
        )
    return _ingestion_agent


def _get_annotation_agent() -> AnnotationAgent:
    global _annotation_agent
    if _annotation_agent is None:
        _annotation_agent = AnnotationAgent(name="annotation_agent")
    return _annotation_agent


def _get_promptgen_agent() -> PromptGenAgent:
    global _promptgen_agent
    if _promptgen_agent is None:
        _promptgen_agent = PromptGenAgent(name="prompt_generator")
    return _promptgen_agent


def _get_refinement_agent() -> RefinementAgent:
    global _refinement_agent
    if _refinement_agent is None:
        _refinement_agent = RefinementAgent(name="refinement")
    return _refinement_agent


def _get_distillation_agent() -> DistillationAgent:
    global _distillation_agent
    if _distillation_agent is None:
        _distillation_agent = DistillationAgent(name="distillation")
    return _distillation_agent


def _convert_to_ingestion_state(state: PipelineState) -> IngestionState:
    return {
        "image_dir": state.get("image_dir", ""),
        "images": [],
        "total_found": 0,
        "duplicates_removed": 0,
        "low_quality_removed": 0,
        "errors": [],
    }


def _convert_to_annotation_state(state: PipelineState) -> AnnotationState:
    return {
        "current_image": state.get("current_image", ""),
        "annotations": {},
        "masks": [],
        "small_target_masks": [],
        "text_prompts": state.get("text_prompts", []),
    }


def _convert_to_prompt_gen_state(state: PipelineState) -> PromptGenState:
    return {
        "current_image": state.get("current_image", ""),
        "text_prompts": [],
        "vlm_raw_response": None,
    }


def _convert_to_refinement_state(state: PipelineState) -> RefinementState:
    annotations = state.get("annotations", {})
    image_height = annotations.get("image_height", 0)
    image_width = annotations.get("image_width", 0)
    return {
        "masks": state.get("masks", []),
        "image_size": (image_height, image_width),
        "refined_masks": [],
    }


def _convert_to_validation_state(state: PipelineState) -> ValidationState:
    return {
        "current_image": state.get("current_image", ""),
        "masks": state.get("masks", []),
        "annotations": state.get("annotations", {}),
        "quality_score": None,
        "evaluation_result": "pass",
        "evaluation_details": {},
    }


def _convert_to_distillation_state(state: PipelineState) -> DistillationState:
    completed = state.get("completed_annotations", [])
    image_paths = [ann.get("image_path") for ann in completed if ann.get("image_path")]
    output_dir = state.get("output_dir", "/tmp/distillation_output")
    generated_prompts = state.get("generated_prompts", [])

    annotations_list = []
    for ann in completed:
        if ann.get("image_path"):
            annotations_list.append(
                {
                    "image_path": ann.get("image_path"),
                    "segments": ann.get("annotations", {}).get("segments", []),
                }
            )

    return {
        "refined_masks": state.get("refined_masks", []),
        "distilled_samples": [],
        "distillation_metrics": {},
        "image_paths": image_paths,
        "output_dir": output_dir,
        "teacher_features": None,
        "tar_shards": [],
        "jsonl_output": "",
        "metadata": {},
        "generated_prompts": generated_prompts,
        "annotations_list": annotations_list,
    }


async def node_ingestion(state: PipelineState) -> PipelineState:
    logger = get_logger("nodes.ingestion")

    if state.get("images") and len(state["images"]) > 0:
        logger.info(f"Using pre-populated images: {len(state['images'])} images")
        state["total_images"] = len(state["images"])
        state["processed_count"] = 0
        state["failed_count"] = 0
        state["errors"] = []
        state["checkpoint"] = {
            "step": 1,
            "timestamp": datetime.now().isoformat(),
            "agent_name": "ingestion",
        }
        return state

    if "output_dir" not in state and "image_dir" in state:
        state["output_dir"] = state["image_dir"].replace("/images", "/output")

    ingestion_state = _convert_to_ingestion_state(state)
    agent = _get_ingestion_agent()

    result = await agent.process(ingestion_state)

    state["images"] = result.get("images", [])
    state["total_images"] = len(result.get("images", []))
    state["processed_count"] = 0
    state["failed_count"] = 0
    state["errors"] = result.get("errors", [])
    state["checkpoint"] = {
        "step": 1,
        "timestamp": datetime.now().isoformat(),
        "agent_name": "ingestion",
    }

    logger.info(f"Ingestion complete: {state['total_images']} images ready")
    return state


async def node_annotation(state: PipelineState) -> PipelineState:
    logger = get_logger("nodes.annotation")

    current_image = state.get("current_image")
    if not current_image:
        logger.warning("No current_image set for annotation")
        return state

    annotation_state = _convert_to_annotation_state(state)
    agent = _get_annotation_agent()

    result = await agent.process(annotation_state)

    state["annotations"] = result.get("annotations", {})
    state["masks"] = result.get("masks", [])
    state["small_target_masks"] = result.get("small_target_masks", [])

    logger.info(
        f"Annotation output: masks={len(state['masks'])}, segments={len(state['annotations'].get('segments', []))}"
    )
    state["checkpoint"] = {
        "step": 2,
        "timestamp": datetime.now().isoformat(),
        "agent_name": "annotation",
    }

    logger.info(f"Annotation complete for {current_image}")
    return state


async def node_prompt_generation(state: PipelineState) -> PipelineState:
    logger = get_logger("nodes.prompt_generation")

    current_image = state.get("current_image")
    if not current_image:
        return state

    quality_tool = QualityCheckTool(min_width=256, min_height=256, min_quality=30)
    if not quality_tool.run(current_image):
        logger.warning(f"Image failed quality check, skipping: {current_image}")
        state["text_prompts"] = []
        state["skipped_low_quality"] = state.get("skipped_low_quality", 0) + 1
        state["current_image"] = None
        return state

    promptgen_state = _convert_to_prompt_gen_state(state)
    agent = _get_promptgen_agent()

    result = await agent.process(promptgen_state)

    state["text_prompts"] = result.get("text_prompts", [])
    state["checkpoint"] = {
        "step": 2,
        "timestamp": datetime.now().isoformat(),
        "agent_name": "prompt_generation",
    }

    logger.info(
        f"Prompt generation complete: {len(state.get('text_prompts', []))} prompts"
    )
    return state


async def node_refinement(state: PipelineState) -> PipelineState:
    logger = get_logger("nodes.refinement")

    refinement_state = _convert_to_refinement_state(state)
    agent = _get_refinement_agent()

    result = await agent.process(refinement_state)

    state["refined_masks"] = result.get("refined_masks", [])
    state["checkpoint"] = {
        "step": 4,
        "timestamp": datetime.now().isoformat(),
        "agent_name": "refinement",
    }

    logger.info(
        f"Refinement complete: {len(state.get('refined_masks', []))} refined masks"
    )
    return state


async def node_validation(state: PipelineState) -> PipelineState:
    logger = get_logger("nodes.validation")

    validation_state = _convert_to_validation_state(state)
    agent = _get_validation_agent()

    result = await agent.process(validation_state)

    state["quality_score"] = result.get("quality_score")
    state["evaluation_result"] = result.get("evaluation_result", "discard")
    state["evaluation_details"] = result.get("evaluation_details", {})
    state["checkpoint"] = {
        "step": 5,
        "timestamp": datetime.now().isoformat(),
        "agent_name": "validation",
    }

    logger.info(
        f"Validation complete: score={state.get('quality_score')}, "
        f"result={state.get('evaluation_result')}"
    )
    return state


async def node_distillation(state: PipelineState) -> PipelineState:
    logger = get_logger("nodes.distillation")

    current_image = state.get("current_image")
    if not current_image:
        state["distilled_samples"] = []
        state["distillation_metrics"] = {}
        return state

    distillation_state = _convert_to_distillation_state(state)
    distillation_state["image_paths"] = [current_image]

    current_segments = state.get("annotations", {}).get("segments", [])
    distillation_state["current_image_segments"] = current_segments

    agent = _get_distillation_agent()

    result = await agent.process(distillation_state)

    state["distilled_samples"] = result.get("distilled_samples", [])
    state["distillation_metrics"] = result.get("distillation_metrics", {})
    state["checkpoint"] = {
        "step": 6,
        "timestamp": datetime.now().isoformat(),
        "agent_name": "distillation",
    }

    annotation_result = {
        "image_path": current_image,
        "annotations": state.get("annotations", {}),
        "quality_score": state.get("quality_score"),
    }
    if "current_image_results" not in state:
        state["current_image_results"] = []
    if "completed_annotations" not in state:
        state["completed_annotations"] = []
    state["current_image_results"].append(annotation_result)
    state["completed_annotations"].append(annotation_result)
    state["processed_count"] += 1

    logger.info(
        f"Distillation complete: {len(state.get('distilled_samples', []))} samples"
    )
    return state


def node_discard(state: PipelineState) -> PipelineState:
    logger = get_logger("nodes.discard")

    current_image = state.get("current_image")
    if current_image:
        if "discarded_samples" not in state:
            state["discarded_samples"] = []
        state["discarded_samples"].append(current_image)
        state["failed_count"] += 1
        state["checkpoint"] = {
            "step": -1,
            "timestamp": datetime.now().isoformat(),
            "agent_name": "discard",
        }

        logger.info(f"Discarded: {current_image}")

    return state


def node_next_image(state: PipelineState) -> PipelineState:
    logger = get_logger("nodes.next_image")

    images = state.get("images", [])
    current_image = state.get("current_image")
    processed_paths = {
        r.get("image_path") for r in state.get("completed_annotations", [])
    }
    discarded_paths = set(state.get("discarded_samples", []))

    next_image = None
    for img in images:
        img_path = img.get("path") if isinstance(img, dict) else str(img)
        if img_path not in processed_paths and img_path not in discarded_paths:
            next_image = img_path
            break

    if next_image:
        state["current_image"] = next_image
        state["iteration_round"] = 0
        logger.info(f"Moving to next image: {next_image}")
    else:
        state["current_image"] = None
        logger.info("No more images to process")

    state["checkpoint"] = {
        "step": 0,
        "timestamp": datetime.now().isoformat(),
        "agent_name": "next_image",
    }

    return state


def node_increment_iteration(state: PipelineState) -> PipelineState:
    state["iteration_round"] = state.get("iteration_round", 0) + 1
    return state
