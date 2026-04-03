"""Edge definitions and conditional routing for the multi-agent pipeline."""

from typing import Literal

from graph.state import PipelineState


MAX_REGENERATION_ROUNDS = 3


def should_regenerate(
    state: PipelineState,
) -> Literal["annotation", "discard", "distillation"]:
    """Determine next step based on validation result.

    Decision logic:
    - If evaluation_result is "pass" -> go to distillation
    - If evaluation_result is "regenerate" and iteration < max -> go to annotation
    - If evaluation_result is "regenerate" and iteration >= max -> discard
    - If evaluation_result is "discard" -> discard immediately

    Args:
        state: Current pipeline state with evaluation_result and iteration_round

    Returns:
        Next node name: "annotation", "discard", or "distillation"
    """
    evaluation_result = state.get("evaluation_result", "discard")
    iteration_round = state.get("iteration_round", 0)

    if evaluation_result == "pass":
        return "distillation"
    elif evaluation_result == "regenerate":
        if iteration_round < MAX_REGENERATION_ROUNDS:
            return "annotation"
        else:
            return "discard"
    else:
        return "discard"


def has_more_images(state: PipelineState) -> bool:
    """Check if there are more images to process.

    Args:
        state: Current pipeline state with images and current_image

    Returns:
        True if more unprocessed images exist, False otherwise
    """
    images = state.get("images", [])
    current_image = state.get("current_image")
    completed = state.get("completed_annotations", [])
    discarded = state.get("discarded_samples", [])

    completed_paths = {r.get("image_path") for r in completed}
    discarded_paths = set(discarded)

    for img in images:
        img_path = img.get("path") if isinstance(img, dict) else str(img)
        if (
            img_path != current_image
            and img_path not in completed_paths
            and img_path not in discarded_paths
        ):
            return True

    return False


def route_after_discard(state: PipelineState) -> Literal["next_image", "__end__"]:
    """Route after discarding an image.

    Args:
        state: Current pipeline state

    Returns:
        "next_image" if more images exist, "__end__" otherwise
    """
    if has_more_images(state):
        return "next_image"
    return "__end__"


def route_after_distillation(state: PipelineState) -> Literal["next_image", "__end__"]:
    """Route after successful distillation.

    Args:
        state: Current pipeline state

    Returns:
        "next_image" if more images exist, "__end__" otherwise
    """
    if has_more_images(state):
        return "next_image"
    return "__end__"


def route_after_next_image(state: PipelineState) -> Literal["annotation", "__end__"]:
    """Route after moving to next image.

    Args:
        state: Current pipeline state

    Returns:
        "annotation" if a next image was set, "__end__" otherwise
    """
    if state.get("current_image"):
        return "annotation"
    return "__end__"


def route_after_ingestion(state: PipelineState) -> Literal["next_image", "__end__"]:
    """Route after ingestion completes.

    Args:
        state: Current pipeline state

    Returns:
        "next_image" if images exist, "__end__" otherwise
    """
    if state.get("images"):
        return "next_image"
    return "__end__"
