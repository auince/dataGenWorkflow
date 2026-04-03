"""Distillation agent for output packaging and tar sharding."""

import json
import os
import tarfile
from pathlib import Path
from typing import Any, Dict, List, TypedDict

import cv2
import numpy as np

from agents.base import BaseAgent
from utils.logger import get_logger


class DistillationState(TypedDict):
    image_paths: List[str]
    teacher_features: Any
    output_dir: str
    tar_shards: List[str]
    jsonl_output: str
    metadata: Dict[str, Any]
    generated_prompts: List[List[str]]
    refined_masks: List[Dict[str, Any]]
    distilled_samples: List[Dict[str, Any]]
    distillation_metrics: Dict[str, float]
    annotations_list: List[Dict[str, Any]]
    current_image_segments: List[Dict[str, Any]]


class DistillationAgent(BaseAgent[DistillationState]):
    IMAGES_PER_SHARD = 1000

    def __init__(
        self, name: str = "distillation", images_per_shard: int = IMAGES_PER_SHARD
    ):
        super().__init__(name)
        self._images_per_shard = images_per_shard
        self.logger = get_logger(f"agents.{name}")

    async def process(self, state: DistillationState) -> DistillationState:
        image_paths = state.get("image_paths", [])
        output_dir = state.get("output_dir", "")

        if not image_paths:
            state["tar_shards"] = []
            state["jsonl_output"] = ""
            return state

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        state = await self._create_tar_shards(state)
        state = await self._write_jsonl_output(state)
        self._save_masks(state)

        return state

    async def _create_tar_shards(self, state: DistillationState) -> DistillationState:
        image_paths = state.get("image_paths", [])
        output_dir = state.get("output_dir", "")

        if not image_paths:
            state["tar_shards"] = []
            return state

        tar_shards = []
        num_images = len(image_paths)
        images_per_shard = self._images_per_shard
        num_shards = (num_images + images_per_shard - 1) // images_per_shard

        for shard_idx in range(num_shards):
            start_idx = shard_idx * images_per_shard
            end_idx = min(start_idx + images_per_shard, num_images)
            shard_images = image_paths[start_idx:end_idx]

            shard_name = f"shard_{shard_idx:04d}.tar"
            shard_path = os.path.join(output_dir, shard_name)

            with tarfile.open(shard_path, "w") as tar:
                for img_path in shard_images:
                    if os.path.exists(img_path):
                        tar.add(img_path, arcname=os.path.basename(img_path))
            tar_shards.append(shard_path)

        state["tar_shards"] = tar_shards
        return state

    async def _write_jsonl_output(self, state: DistillationState) -> DistillationState:
        image_paths = state.get("image_paths", [])
        output_dir = state.get("output_dir", "")
        generated_prompts = state.get("generated_prompts", [])
        refined_masks = state.get("refined_masks", [])

        jsonl_path = os.path.join(output_dir, "annotations.jsonl")
        distilled_samples = []

        with open(jsonl_path, "w") as f:
            for idx, img_path in enumerate(image_paths):
                record = {
                    "image_path": img_path,
                    "image_name": os.path.basename(img_path),
                }

                if idx < len(generated_prompts):
                    record["prompts"] = generated_prompts[idx]

                if idx < len(refined_masks):
                    mask_data = refined_masks[idx]
                    if isinstance(mask_data, dict):
                        record["mask_count"] = mask_data.get("count", 0)

                f.write(json.dumps(record) + "\n")
                distilled_samples.append(record)

        state["jsonl_output"] = jsonl_path
        state["distilled_samples"] = distilled_samples
        return state

    def _save_masks(self, state: DistillationState) -> None:
        """Save masks and overlay visualizations."""
        image_paths = state.get("image_paths", [])
        current_segments = state.get("current_image_segments", [])
        output_dir = state.get("output_dir", "")

        mask_dir = os.path.join(output_dir, "masks")
        overlay_dir = os.path.join(output_dir, "overlays")
        os.makedirs(mask_dir, exist_ok=True)
        os.makedirs(overlay_dir, exist_ok=True)

        if not current_segments:
            self.logger.warning("No current_image_segments found in state")
            return

        for img_path in image_paths:
            if not os.path.exists(img_path):
                continue

            base_name = os.path.splitext(os.path.basename(img_path))[0]
            img = cv2.imread(img_path)
            if img is None:
                continue
            h, w = img.shape[:2]

            masks_by_concept = {}

            for seg in current_segments:
                concept = seg.get("concept", "unknown")
                mask = seg.get("mask")

                if mask is None:
                    continue

                if concept not in masks_by_concept:
                    masks_by_concept[concept] = []
                masks_by_concept[concept].append(mask)

            colors = [
                (255, 0, 0),
                (0, 255, 0),
                (0, 0, 255),
                (255, 255, 0),
                (255, 0, 255),
                (0, 255, 255),
            ]

            overlay = img.copy()
            concept_idx = 0
            for concept, masks in masks_by_concept.items():
                combined_mask = np.zeros((h, w), dtype=np.uint8)
                for m in masks:
                    m_resized = m
                    if m.shape[:2] != (h, w):
                        m_resized = cv2.resize(m, (w, h))
                    if m_resized.dtype != np.uint8:
                        m_resized = (m_resized > 0).astype(np.uint8)
                    combined_mask = np.maximum(combined_mask, m_resized)

                concept_filename = f"{base_name}_{concept}.png"
                concept_path = os.path.join(mask_dir, concept_filename)
                cv2.imwrite(concept_path, combined_mask * 255)

                color = colors[concept_idx % len(colors)]
                mask_bool = combined_mask.astype(bool)
                overlay[mask_bool] = (
                    overlay[mask_bool].astype(np.float32) * 0.5
                    + np.array(color, dtype=np.float32) * 0.5
                ).astype(np.uint8)

                contours, _ = cv2.findContours(
                    combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                cv2.drawContours(overlay, contours, -1, color, 2)
                cv2.putText(
                    overlay,
                    concept,
                    (10, 30 + concept_idx * 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2,
                )
                concept_idx += 1

            overlay_path = os.path.join(overlay_dir, f"{base_name}_overlay.jpg")
            cv2.imwrite(overlay_path, overlay)
            self.logger.info(f"Saved overlay: {base_name}_overlay.jpg")
