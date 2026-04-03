"""ValidationAgent for VLM-based quality evaluation of generated masks."""

import base64
import json
import os
from typing import TypedDict, Optional, List, Dict, Any

import cv2
import numpy as np

from agents.base import BaseAgent
from utils.logger import get_logger
from utils.vlm_client import call_vlm

# Iteration control constants
MAX_ITERATIONS = 3


def should_terminate(state: dict) -> bool:
    """Check if iteration should terminate based on round count.

    Args:
        state: Dictionary containing iteration_round.

    Returns:
        True if iteration_round >= MAX_ITERATIONS, False otherwise.
    """
    iteration_round = state.get("iteration_round", 0)
    return iteration_round >= MAX_ITERATIONS


def get_regenerate_params(round: int) -> dict:
    """Get adjusted SAM3 parameters for regeneration based on iteration round.

    Args:
        round: Current iteration round (1-indexed).

    Returns:
        Dictionary with adjusted conf_threshold, iou_threshold, scale_strategy.
    """
    # Progressive relaxation of thresholds across rounds
    base_conf = 0.25
    base_iou = 0.7

    if round == 1:
        conf_threshold = base_conf
        iou_threshold = base_iou
        scale_strategy = "original"
    elif round == 2:
        conf_threshold = max(0.15, base_conf - 0.1)
        iou_threshold = max(0.5, base_iou - 0.15)
        scale_strategy = "multi_scale"
    else:  # round >= 3
        conf_threshold = max(0.10, base_conf - 0.15)
        iou_threshold = max(0.4, base_iou - 0.25)
        scale_strategy = "multi_scale"

    return {
        "conf_threshold": conf_threshold,
        "iou_threshold": iou_threshold,
        "scale_strategy": scale_strategy,
    }


def quality_gate(scores: dict) -> str:
    """Check if quality scores meet the pass threshold.

    Args:
        scores: Dictionary of dimension scores.

    Returns:
        "pass" if average score >= 7, else "fail".
    """
    if not scores:
        return "fail"
    avg_score = sum(scores.values()) / len(scores)
    return "pass" if avg_score >= 7 else "fail"


class ValidationState(TypedDict):
    """State schema for ValidationAgent."""

    current_image: str
    masks: List[np.ndarray]
    annotations: dict
    quality_score: Optional[float]
    evaluation_result: str  # "pass", "regenerate", "discard"
    evaluation_details: Dict[str, Any]


class ValidationAgent(BaseAgent[ValidationState]):
    """Agent for VLM-based quality evaluation of segmentation masks.

    Uses VLM to evaluate masks across 5 dimensions:
    1. Mask completeness - Are all objects fully segmented?
    2. Boundary accuracy - Are boundaries crisp and accurate?
    3. Text-mask alignment - Does mask match the text description?
    4. False positive detection - Are there spurious mask regions?
    5. Small target detection - Are small targets properly captured?

    Decision thresholds:
    - score >= 7: pass (use masks)
    - score 5-6: regenerate (needs improvement)
    - score < 5: discard (quality too poor)
    """

    # Evaluation dimension weights
    DIMENSION_WEIGHTS = {
        "mask_completeness": 0.25,
        "boundary_accuracy": 0.20,
        "text_mask_alignment": 0.20,
        "false_positive_detection": 0.15,
        "small_target_detection": 0.20,
    }

    # Decision thresholds
    PASS_THRESHOLD = 7.0
    REGENERATE_THRESHOLD = 5.0

    def __init__(
        self,
        name: str = "validation_agent",
        model: str = "kimi-vl-alpha",
    ):
        """Initialize ValidationAgent.

        Args:
            name: Agent name.
            model: VLM model identifier.
        """
        super().__init__(name)
        self.model = model
        self.logger = get_logger(f"agents.{name}")

    def _create_evaluation_prompt(
        self, image: np.ndarray, masks: List[np.ndarray], annotations: dict
    ) -> str:
        """Create evaluation prompt for VLM.

        Args:
            image: Input image.
            masks: List of segmentation masks.
            annotations: Annotation dictionary with text descriptions.

        Returns:
            Formatted prompt string for VLM evaluation.
        """
        num_masks = len(masks)
        has_small_targets = annotations.get("has_small_targets", False)

        prompt = f"""You are an expert quality evaluator for image segmentation masks.

Evaluate the following segmentation result across 5 dimensions (score 1-10 each):

1. **Mask Completeness** (weight 25%): Are all visible objects fully and correctly segmented? Missing regions = low score.

2. **Boundary Accuracy** (weight 20%): Are mask boundaries crisp, smooth, and aligned with actual object edges? Jagged/overlapping boundaries = low score.

3. **Text-Mask Alignment** (weight 20%): Does the segmentation match the text description "{annotations.get("description", "N/A")}"? Mismatched objects = low score.

4. **False Positive Detection** (weight 15%): Are there spurious mask regions that don't correspond to real objects? Many false positives = low score.

5. **Small Target Detection** (weight 20%): {"Small targets (8x8 pixels or smaller) are present and should be properly segmented." if has_small_targets else "No small targets expected."} Missing small targets = low score.

Image info: {image.shape[1]}x{image.shape[0]} pixels, {num_masks} mask(s) detected.

Return your evaluation as JSON:
{{
  "mask_completeness": <score 1-10>,
  "boundary_accuracy": <score 1-10>,
  "text_mask_alignment": <score 1-10>,
  "false_positive_detection": <score 1-10>,
  "small_target_detection": <score 1-10>,
  "reasoning": "<brief explanation of scores>"
}}"""
        return prompt

    async def _call_kimi_vlm(
        self, image: np.ndarray, prompt: str
    ) -> Optional[Dict[str, Any]]:
        """Call VLM for evaluation.

        Args:
            image: Input image (RGB np.ndarray).
            prompt: Evaluation prompt.

        Returns:
            Parsed JSON response or None on error.
        """
        try:
            _, buffer = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            img_base64 = base64.b64encode(buffer).decode("utf-8")
            response_text = call_vlm(img_base64, prompt)

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            return json.loads(response_text.strip())

        except Exception as e:
            self.logger.error(f"VLM call failed: {e}")
            return None

    def _calculate_weighted_score(self, dimension_scores: Dict[str, float]) -> float:
        """Calculate weighted quality score.

        Args:
            dimension_scores: Dictionary of dimension -> score.

        Returns:
            Weighted average score (0-10).
        """
        total_score = 0.0
        for dimension, weight in self.DIMENSION_WEIGHTS.items():
            score = dimension_scores.get(dimension, 5.0)  # Default 5 if missing
            total_score += score * weight
        return total_score

    def _get_evaluation_result(self, score: float) -> str:
        """Determine evaluation result based on score.

        Args:
            score: Quality score (0-10).

        Returns:
            "pass", "regenerate", or "discard".
        """
        if score >= self.PASS_THRESHOLD:
            return "pass"
        elif score >= self.REGENERATE_THRESHOLD:
            return "regenerate"
        else:
            return "discard"

    async def process(self, state: ValidationState) -> ValidationState:
        """Evaluate segmentation quality using VLM.

        Args:
            state: Current state with image, masks, and annotations.

        Returns:
            Updated state with quality_score and evaluation_result.
        """
        image_path = state.get("current_image")
        masks = state.get("masks", [])
        annotations = state.get("annotations", {})

        if not image_path:
            state["quality_score"] = 0.0
            state["evaluation_result"] = "discard"
            state["evaluation_details"] = {"error": "No image provided"}
            return state

        if not masks:
            state["quality_score"] = 0.0
            state["evaluation_result"] = "discard"
            state["evaluation_details"] = {"error": "No masks to evaluate"}
            return state

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            state["quality_score"] = 0.0
            state["evaluation_result"] = "discard"
            state["evaluation_details"] = {"error": "Failed to load image"}
            return state

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Create evaluation prompt
        prompt = self._create_evaluation_prompt(image_rgb, masks, annotations)

        # Call VLM API
        vlm_result = await self._call_kimi_vlm(image_rgb, prompt)

        if vlm_result is None:
            # Fallback to heuristic evaluation
            self.logger.info("Using heuristic evaluation fallback")
            dimension_scores = self._heuristic_evaluation(image_rgb, masks, annotations)
        else:
            dimension_scores = {
                "mask_completeness": vlm_result.get("mask_completeness", 5.0),
                "boundary_accuracy": vlm_result.get("boundary_accuracy", 5.0),
                "text_mask_alignment": vlm_result.get("text_mask_alignment", 5.0),
                "false_positive_detection": vlm_result.get(
                    "false_positive_detection", 5.0
                ),
                "small_target_detection": vlm_result.get("small_target_detection", 5.0),
            }

        # Calculate weighted score
        quality_score = self._calculate_weighted_score(dimension_scores)
        evaluation_result = self._get_evaluation_result(quality_score)

        state["quality_score"] = quality_score
        state["evaluation_result"] = evaluation_result
        state["evaluation_details"] = {
            "dimension_scores": dimension_scores,
            "reasoning": vlm_result.get("reasoning", "Heuristic evaluation")
            if vlm_result
            else "Heuristic evaluation",
        }

        self.logger.info(
            f"Validation complete: score={quality_score:.2f}, result={evaluation_result}"
        )

        self._save_validation_visualization(image_path, masks, state)

        return state

    def _save_validation_visualization(
        self, image_path: str, masks: List[np.ndarray], state: ValidationState
    ) -> None:
        """Save visualization of validation and segmentation results."""
        try:
            from utils.visualizer import (
                visualize_segmentation_result,
                visualize_validation_panel,
            )

            output_dir = "/data/lch/SAM/dataGenAgent/output"
            vis_dir = os.path.join(output_dir, "visualizations")
            os.makedirs(vis_dir, exist_ok=True)

            base_name = os.path.splitext(os.path.basename(image_path))[0]

            prompt = state.get("evaluation_details", {}).get("reasoning", "No prompt")
            if isinstance(prompt, list):
                prompt = " ".join(str(p) for p in prompt)

            seg_path = os.path.join(vis_dir, f"{base_name}_segmentation.jpg")
            visualize_segmentation_result(
                image_path, masks, prompt, output_path=seg_path
            )

            val_result = {
                "quality_score": state.get("quality_score", 0),
                "evaluation_details": state.get("evaluation_details", {}),
                "evaluation_result": state.get("evaluation_result", "unknown"),
            }
            val_path = os.path.join(vis_dir, f"{base_name}_validation.jpg")
            visualize_validation_panel(
                image_path, masks, val_result, output_path=val_path
            )

            self.logger.info(f"Saved visualizations: {seg_path}, {val_path}")

        except Exception as e:
            self.logger.warning(f"Failed to save visualization: {e}")

    def _heuristic_evaluation(
        self, image: np.ndarray, masks: List[np.ndarray], annotations: dict
    ) -> Dict[str, float]:
        """Fallback heuristic evaluation when API is unavailable.

        Args:
            image: Input image.
            masks: List of masks.
            annotations: Annotation dictionary.

        Returns:
            Dictionary of dimension scores.
        """
        scores = {}

        # 1. Mask completeness - based on mask count vs expected
        expected_count = annotations.get("expected_objects", 1)
        actual_count = len(masks)
        if actual_count >= expected_count:
            scores["mask_completeness"] = min(
                8.0, 5.0 + (actual_count - expected_count)
            )
        else:
            scores["mask_completeness"] = max(
                2.0, 5.0 - (expected_count - actual_count) * 2
            )

        # 2. Boundary accuracy - based on mask smoothness
        boundary_scores = []
        for mask in masks:
            if mask.dtype != np.uint8:
                mask_binary = (mask > 0).astype(np.uint8)
            else:
                mask_binary = mask

            # Calculate perimeter and area ratio (rough measure of smoothness)
            contours, _ = cv2.findContours(
                mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if contours:
                perimeter = cv2.arcLength(contours[0], True)
                area = cv2.contourArea(contours[0])
                if area > 0:
                    # Circularity: 4 * pi * area / perimeter^2
                    circularity = (
                        4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0
                    )
                    boundary_scores.append(min(10.0, circularity * 10))

        scores["boundary_accuracy"] = (
            np.mean(boundary_scores) if boundary_scores else 5.0
        )

        # 3. Text-mask alignment - default moderate score (no text available)
        scores["text_mask_alignment"] = 6.0

        # 4. False positive detection - based on mask area distribution
        h, w = image.shape[:2]
        total_image_area = h * w
        mask_areas = []

        for mask in masks:
            mask_binary = (mask > 0).astype(np.uint8)
            mask_area = np.sum(mask_binary)
            mask_areas.append(mask_area / total_image_area)

        # High coverage or very uneven distribution suggests false positives
        avg_coverage = np.mean(mask_areas) if mask_areas else 0
        std_coverage = np.std(mask_areas) if len(mask_areas) > 1 else 0

        if avg_coverage > 0.5:
            scores["false_positive_detection"] = 3.0  # Too much coverage
        elif std_coverage > 0.2:
            scores["false_positive_detection"] = 5.0  # Uneven
        else:
            scores["false_positive_detection"] = 7.0

        # 5. Small target detection - check if small masks exist
        small_target_threshold = 8 * 8  # 8x8 pixels
        small_count = 0
        for mask in masks:
            mask_binary = (mask > 0).astype(np.uint8)
            area = np.sum(mask_binary)
            if area <= small_target_threshold and area > 0:
                small_count += 1

        has_small_in_annotation = annotations.get("has_small_targets", False)
        if has_small_in_annotation:
            if small_count > 0:
                scores["small_target_detection"] = 8.0
            else:
                scores["small_target_detection"] = 3.0
        else:
            if small_count > len(masks) * 0.3:
                scores["small_target_detection"] = 5.0  # Too many small
            else:
                scores["small_target_detection"] = 7.0

        return scores
