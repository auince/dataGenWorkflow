"""Refinement agent for mask post-processing."""

from typing import Any, Dict, List, Tuple, TypedDict

import cv2
import numpy as np

from agents.base import BaseAgent
from utils.rle import encode_mask


class RefinementState(TypedDict):
    """State schema for RefinementAgent."""

    masks: List[np.ndarray]
    image_size: Tuple[int, int]
    refined_masks: List[Dict[str, Any]]


class RefinementAgent(BaseAgent[RefinementState]):
    """Agent that refines masks using morphology and filtering.

    Applies the following refinements:
    - Morphology processing (opening/closing)
    - Area filtering (removes masks <4 pixels or >90% of image)
    - Boundary refinement (smoothing)
    - RLE encoding for COCO format
    """

    def __init__(self, name: str = "refinement"):
        """Initialize RefinementAgent.

        Args:
            name: Agent name
        """
        super().__init__(name)
        self._min_area = 4  # Minimum 4 pixels
        self._max_area_ratio = 0.90  # Maximum 90% of image area

    async def process(self, state: RefinementState) -> RefinementState:
        """Process masks through refinement pipeline.

        Args:
            state: State containing masks and image size

        Returns:
            Updated state with refined masks in RLE format
        """
        masks = state.get("masks", [])
        image_size = state.get("image_size", (0, 0))
        height, width = image_size

        if not masks:
            state["refined_masks"] = []
            return state

        refined_masks = []

        for mask in masks:
            # Step 1: Morphology processing
            processed = self._morphology_process(mask)

            # Step 2: Area filtering
            if not self._area_filter(processed, height * width):
                continue

            # Step 3: Boundary refinement
            smoothed = self._boundary_refinement(processed)

            # Step 4: RLE encoding
            rle = encode_mask(smoothed)

            refined_masks.append(
                {
                    "rle": rle,
                    "size": (height, width),
                    "area": int(np.sum(smoothed)),
                }
            )

        state["refined_masks"] = refined_masks
        return state

    def _morphology_process(self, mask: np.ndarray) -> np.ndarray:
        """Apply morphology operations to mask.

        Uses opening (erosion followed by dilation) to remove noise,
        then closing (dilation followed by erosion) to fill holes.

        Args:
            mask: Binary mask

        Returns:
            Processed binary mask
        """
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        # Convert boolean to uint8 for OpenCV compatibility
        if mask.dtype == bool:
            mask = mask.astype(np.uint8)

        # Opening: removes small noise
        opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        # Closing: fills small holes
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)

        return closed

    def _area_filter(self, mask: np.ndarray, total_area: int) -> bool:
        """Filter masks by area.

        Removes masks that are:
        - Smaller than 4 pixels
        - Larger than 90% of image area

        Args:
            mask: Binary mask
            total_area: Total image area in pixels

        Returns:
            True if mask passes filter, False otherwise
        """
        area = np.sum(mask)

        # Filter: too small
        if area < self._min_area:
            return False

        # Filter: too large (>90% of image)
        if area > total_area * self._max_area_ratio:
            return False

        return True

    def _boundary_refinement(self, mask: np.ndarray) -> np.ndarray:
        """Refine mask boundary smoothing.

        Applies morphological smoothing to reduce boundary irregularity.

        Args:
            mask: Binary mask

        Returns:
            Boundary-refined mask
        """
        # Use Gaussian blur on the mask to smooth boundaries
        smoothed = cv2.GaussianBlur(mask.astype(np.float32), (5, 5), 0)

        # Threshold back to binary (using midpoint to preserve some smoothing)
        binary = (smoothed > 0.5).astype(np.uint8)

        return binary
