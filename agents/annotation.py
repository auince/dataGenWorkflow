from typing import TypedDict, List, Dict, Any

import cv2
import numpy as np
import torch

from agents.base import BaseAgent


class AnnotationState(TypedDict):
    current_image: str
    annotations: dict
    masks: list
    small_target_masks: list
    text_prompts: List[str]


class MaskWithConcept(TypedDict):
    mask: np.ndarray
    concept: str
    instance_id: int
    bbox: List[float]
    score: float


class AnnotationAgent(BaseAgent[AnnotationState]):
    def __init__(
        self,
        name: str = "annotation_agent",
        model_path: str = "/data/lch/SAM/ultralytics-main/sam3.pt",
        device: str = None,
    ):
        super().__init__(name)
        self.model_path = model_path
        self.device = device or ("cuda:1" if torch.cuda.is_available() else "cpu")
        self.predictor = None

    def _load_model(self):
        if self.predictor is None:
            from ultralytics.models.sam import SAM3SemanticPredictor

            self.predictor = SAM3SemanticPredictor(
                overrides={
                    "model": self.model_path,
                    "task": "segment",
                    "mode": "predict",
                    "device": self.device,
                    "verbose": False,
                    "save": False,
                }
            )

    async def process(self, state: AnnotationState) -> AnnotationState:
        image_path = state.get("current_image")
        text_prompts = state.get("text_prompts", [])

        if not image_path:
            state["annotations"] = {}
            state["masks"] = []
            state["small_target_masks"] = []
            return state

        if not text_prompts:
            text_prompts = ["object"]

        self._load_model()

        image = cv2.imread(image_path)
        if image is None:
            state["annotations"] = {}
            state["masks"] = []
            state["small_target_masks"] = []
            return state

        results = self.predictor(source=image_path, text=text_prompts)
        if not results:
            state["annotations"] = {}
            state["masks"] = []
            state["small_target_masks"] = []
            return state

        r = results[0]

        masks_with_concepts = self._extract_masks_per_concept(r, text_prompts)

        all_masks = []
        annotations_list = []

        for concept, mask_data in masks_with_concepts.items():
            for idx, (mask, bbox, score) in enumerate(mask_data):
                mask_uint8 = (
                    (mask > 0).astype(np.uint8) if mask.dtype != np.uint8 else mask
                )
                all_masks.append(mask_uint8)

                annotations_list.append(
                    {
                        "concept": concept,
                        "instance_id": idx,
                        "mask": mask_uint8,
                        "bbox": bbox,
                        "score": float(score),
                        "orig_bbox": bbox,
                    }
                )

        state["masks"] = all_masks
        state["annotations"] = {
            "image_height": image.shape[0],
            "image_width": image.shape[1],
            "segments": annotations_list,
            "num_concepts": len(masks_with_concepts),
            "total_instances": len(all_masks),
        }

        small_thresh = 8 * 8
        small_target_masks = []
        for ann in annotations_list:
            mask = ann["mask"]
            area = np.sum(mask)
            if 0 < area <= small_thresh:
                small_target_masks.append(ann)

        state["small_target_masks"] = small_target_masks

        return state

    def _extract_masks_per_concept(
        self, result, text_prompts: List[str]
    ) -> Dict[str, List]:
        masks_per_concept = {}

        if not hasattr(result, "masks") or result.masks is None:
            return masks_per_concept

        masks_data = result.masks.data.cpu().numpy()
        boxes = result.boxes
        cls_tensor = boxes.cls.cpu().numpy() if boxes is not None else []
        conf_tensor = boxes.conf.cpu().numpy() if boxes is not None else []

        names = (
            result.names if hasattr(result, "names") and result.names else text_prompts
        )

        for idx in range(len(masks_data)):
            if idx >= len(cls_tensor):
                concept_idx = 0
            else:
                concept_idx = int(cls_tensor[idx])

            if concept_idx < len(names):
                concept = names[concept_idx]
            else:
                concept = names[0] if names else "object"

            mask = masks_data[idx]
            h, w = mask.shape

            if idx < len(boxes.xyxy):
                x1, y1, x2, y2 = boxes.xyxy[idx].cpu().numpy()
                bbox = [float(x1), float(y1), float(x2 - x1), float(y2 - y1)]
            else:
                contours, _ = cv2.findContours(
                    (mask * 255).astype(np.uint8),
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE,
                )
                if contours:
                    x, y, w, h = cv2.boundingRect(contours[0])
                    bbox = [float(x), float(y), float(w), float(h)]
                else:
                    bbox = [0, 0, float(w), float(h)]

            score = float(conf_tensor[idx]) if idx < len(conf_tensor) else 1.0

            if concept not in masks_per_concept:
                masks_per_concept[concept] = []
            masks_per_concept[concept].append((mask, bbox, score))

        return masks_per_concept

    def segment_with_points(self, image: np.ndarray, points: list, labels: list = None):
        raise NotImplementedError(
            "Point-based segmentation not implemented in text-prompt mode"
        )

    def segment_with_bbox(self, image: np.ndarray, bboxes: list):
        raise NotImplementedError(
            "Bbox-based segmentation not implemented in text-prompt mode"
        )
