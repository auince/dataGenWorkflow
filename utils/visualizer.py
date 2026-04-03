"""Visualization utilities for pipeline results."""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import cv2
import numpy as np


def draw_prompt_on_image(
    img: np.ndarray, prompt: str, position: str = "bottom"
) -> np.ndarray:
    """Draw prompt text on image."""
    h, w = img.shape[:2]
    result = img.copy()

    max_width = w - 40
    font_scale = 0.5
    thickness = 1

    words = prompt.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        (test_width, _), _ = cv2.getTextSize(
            test_line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    line_height = 20
    box_height = len(lines) * line_height + 10

    if position == "bottom":
        y_start = max(0, h - box_height - 5)
    else:
        y_start = 5

    cv2.rectangle(
        result, (5, y_start), (w - 5, min(h, y_start + box_height)), (0, 0, 0), -1
    )
    cv2.rectangle(
        result, (5, y_start), (w - 5, min(h, y_start + box_height)), (255, 255, 255), 1
    )

    for i, line in enumerate(lines):
        y = y_start + 15 + i * line_height
        if y < h - 5:
            cv2.putText(
                result,
                line[:60],
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),
                thickness,
            )

    return result


def visualize_segmentation_result(
    image_path: str,
    masks: List[np.ndarray],
    prompt: str,
    class_names: Optional[List[str]] = None,
    output_path: str = None,
) -> bool:
    """Create visualization: original + masks overlay + prompt."""
    img = cv2.imread(image_path)
    if img is None:
        return False

    h, w = img.shape[:2]

    overlay = img.copy()
    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
    ]

    for idx, mask in enumerate(masks):
        if mask is None or mask.size == 0:
            continue

        mask_uint8 = (mask > 0).astype(np.uint8) if mask.dtype != np.uint8 else mask
        if mask_uint8.shape[:2] != (h, w):
            mask_uint8 = cv2.resize(mask_uint8, (w, h))

        color = colors[idx % len(colors)]
        mask_bool = mask_uint8.astype(bool)
        overlay[mask_bool] = color

        contours, _ = cv2.findContours(
            mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(overlay, contours, -1, color, 2)

        M = cv2.moments(mask_uint8)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            label = (
                class_names[idx]
                if class_names and idx < len(class_names)
                else f"O{idx + 1}"
            )
            cv2.putText(
                overlay, label, (cx - 15, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
            )

    img_with_prompt = draw_prompt_on_image(overlay, prompt, position="bottom")

    result_img = np.hstack([img, img_with_prompt])

    cv2.putText(
        result_img,
        "Original",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        1,
    )
    cv2.putText(
        result_img,
        "Mask+Prompt",
        (w + 10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        1,
    )

    legend_x = w + 10
    legend_y = 50
    for idx, mask in enumerate(masks[:6]):
        if mask is None or mask.size == 0:
            continue
        color = colors[idx % len(colors)]
        label = (
            class_names[idx]
            if class_names and idx < len(class_names)
            else f"Object {idx + 1}"
        )
        cv2.rectangle(
            result_img, (legend_x, legend_y), (legend_x + 15, legend_y + 15), color, -1
        )
        cv2.putText(
            result_img,
            label[:15],
            (legend_x + 20, legend_y + 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 255, 255),
            1,
        )
        legend_y += 20

    if output_path:
        cv2.imwrite(output_path, result_img)

    return True


def visualize_validation_panel(
    image_path: str,
    masks: List[np.ndarray],
    validation_result: Dict[str, Any],
    output_path: str = None,
) -> bool:
    """Create validation visualization panel."""
    img = cv2.imread(image_path)
    if img is None:
        return False

    h, w = img.shape[:2]
    panel_width = 350
    panel = np.zeros((h, panel_width, 3), dtype=np.uint8)
    panel[:] = (50, 50, 50)

    quality_score = validation_result.get("quality_score", 0)
    eval_result = validation_result.get("evaluation_result", "unknown")

    cv2.putText(
        panel,
        "Validation Results",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    color = (
        (0, 255, 0)
        if eval_result == "pass"
        else (0, 0, 255)
        if eval_result == "fail"
        else (0, 255, 255)
    )
    cv2.putText(
        panel,
        f"Score: {quality_score:.2f}/10",
        (10, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2,
    )
    cv2.putText(
        panel,
        f"Result: {eval_result.upper()}",
        (10, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2,
    )

    scores = validation_result.get("evaluation_details", {}).get("dimension_scores", {})
    y = 130
    for dim, score in scores.items():
        dim_label = dim.replace("_", " ").title()[:18]
        bar_x = 130
        bar_width = int((score / 10.0) * (panel_width - 150))
        cv2.putText(
            panel,
            dim_label,
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (200, 200, 200),
            1,
        )
        cv2.rectangle(
            panel, (bar_x, y - 10), (bar_x + bar_width, y + 2), (0, 200, 0), -1
        )
        cv2.putText(
            panel,
            f"{score:.1f}",
            (bar_x + bar_width + 5, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (255, 255, 255),
            1,
        )
        y += 22

    result_img = np.hstack([img, panel])

    if output_path:
        cv2.imwrite(output_path, result_img)

    return True


def save_pipeline_outputs(
    image_paths: List[str],
    masks_list: List[List[np.ndarray]],
    prompts_list: List[str],
    validation_results: List[Dict[str, Any]],
    output_dir: str = "/data/lch/SAM/dataGenAgent/output",
) -> Dict[str, Any]:
    """Save all pipeline visualizations to /data/lch/SAM/dataGenAgent/output/."""
    vis_dir = os.path.join(output_dir, "visualizations")
    os.makedirs(vis_dir, exist_ok=True)

    paths = {"visualization_dir": vis_dir, "images": []}

    for idx, (img_path, masks, prompt, val_result) in enumerate(
        zip(image_paths, masks_list, prompts_list, validation_results)
    ):
        base_name = os.path.splitext(os.path.basename(img_path))[0]

        seg_viz_path = os.path.join(vis_dir, f"{base_name}_segmentation.jpg")
        visualize_segmentation_result(img_path, masks, prompt, output_path=seg_viz_path)

        val_viz_path = os.path.join(vis_dir, f"{base_name}_validation.jpg")
        visualize_validation_panel(
            img_path, masks, val_result, output_path=val_viz_path
        )

        paths["images"].append(
            {
                "original": img_path,
                "segmentation": seg_viz_path,
                "validation": val_viz_path,
                "prompt": prompt,
            }
        )

    summary_path = os.path.join(vis_dir, "visualization_summary.json")
    with open(summary_path, "w") as f:
        json.dump(paths, f, indent=2, default=str)
    paths["summary"] = summary_path

    return paths
