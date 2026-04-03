#!/usr/bin/env python3
import asyncio
import base64
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

log_dir = Path("/data/lch/SAM/datasets/训练集")
log_file = log_dir / f"annotation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

sys.path.insert(0, "/data/lch/SAM/dataGenWorkflow")

from graph.pipeline import create_workflow
from main import initialize_state

BATCH_SIZE = 100


def get_processed_images(output_path: Path, input_path: Path = None) -> set:
    processed = set()

    jsonl_file = output_path / "annotations.jsonl"
    if jsonl_file.exists():
        with open(jsonl_file) as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if "image_path" in record:
                        processed.add(record["image_path"])
                except json.JSONDecodeError:
                    continue

    mask_dir = output_path / "masks"
    if mask_dir.exists() and input_path:
        stem_to_image = {}
        for img_file in input_path.iterdir():
            if img_file.is_file():
                stem_to_image[img_file.stem] = str(img_file)

        for mask_file in mask_dir.iterdir():
            if mask_file.is_file() and mask_file.suffix == ".png":
                img_stem = mask_file.stem
                parts = img_stem.rsplit("_", 1)
                if len(parts) >= 1:
                    img_stem = parts[0]
                if img_stem in stem_to_image:
                    processed.add(stem_to_image[img_stem])

    return processed


class VLMCache:
    PROMPT_TEMPLATE = """Analyze this infrared/thermal image and identify the main concepts/objects that can be segmented.

Requirements:
- Generate 1-10 short concept labels (1-3 words each)
- Cover different scales: large objects AND small targets
- Use specific terms (e.g., "person" not "human", "car" not "vehicle")
- Focus on distinct, separable objects
- Only output concepts visible in the image

Return JSON format:
{{
  "concepts": ["concept1", "concept2", "concept3", ...]
}}

Only return valid JSON, no explanation."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, image_path: str) -> str:
        img_name = Path(image_path).stem
        return f"vlm_{img_name}.json"

    def _get_cache_path(self, image_path: str) -> Path:
        return self.cache_dir / self._get_cache_key(image_path)

    def get(self, image_path: str) -> dict | None:
        cache_path = self._get_cache_path(image_path)
        if cache_path.exists():
            try:
                with open(cache_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def set(self, image_path: str, concepts: list, raw_response: str):
        cache_path = self._get_cache_path(image_path)
        try:
            with open(cache_path, "w") as f:
                json.dump({"concepts": concepts, "raw_response": raw_response}, f)
        except IOError as e:
            logger.warning(f"Failed to save VLM cache for {image_path}: {e}")

    async def prefetch(self, image_paths: list[str]):
        from utils.vlm_client import call_vlm
        import cv2

        semaphore = asyncio.Semaphore(32)

        async def fetch_one(image_path: str):
            if self.get(image_path) is not None:
                return
            async with semaphore:
                try:
                    image = cv2.imread(image_path)
                    if image is None:
                        return
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    _, buffer = cv2.imencode(".png", image_rgb)
                    img_base64 = base64.b64encode(buffer).decode("utf-8")

                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None, call_vlm, img_base64, self.PROMPT_TEMPLATE
                    )

                    concepts = self._parse_response(response)
                    self.set(image_path, concepts, response)
                    logger.info(f"VLM cached: {Path(image_path).name}")
                except Exception as e:
                    logger.warning(f"VLM prefetch failed for {image_path}: {e}")

        tasks = [fetch_one(p) for p in image_paths]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _parse_response(self, response: str) -> list:
        import re

        content = response.strip()
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0]
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0]
        content = content.strip()

        try:
            data = json.loads(content)
            concepts = data.get("concepts", [])
            if isinstance(concepts, list) and concepts:
                concepts = [str(c).strip() for c in concepts if str(c).strip()]
                if concepts:
                    return concepts
        except json.JSONDecodeError:
            pass

        patterns = [r'"([^"]+)"', r"'([^']+)'", r"\[([^\]]+)\]"]
        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                concepts_str = matches[-1]
                concepts = [
                    c.strip().strip('"').strip("'") for c in concepts_str.split(",")
                ]
                concepts = [c for c in concepts if c]
                if concepts:
                    return concepts

        lines = [l.strip() for l in content.split("\n") if l.strip()]
        concepts = []
        for line in lines:
            for prefix in ["concepts:", "- ", "* ", "• "]:
                if line.startswith(prefix):
                    line = line[len(prefix) :]
            line = line.strip().strip(",").strip()
            if line and len(line) < 30:
                concepts.append(line)

        return concepts[:10] if concepts else ["object"]


async def process_batch(
    input_path: Path,
    output_path: Path,
    dataset_name: str,
    batch_idx: int,
    offset: int,
    completed_annotations: list,
    vlm_cache: VLMCache,
):
    app = create_workflow()
    state = initialize_state(
        input_path,
        max_images=BATCH_SIZE,
        checkpoint_data=None,
        offset=offset,
        completed_annotations=completed_annotations,
    )
    state["output_dir"] = str(output_path)
    state["vlm_cache_dir"] = str(vlm_cache.cache_dir)

    workflow_input = {
        "image_dir": str(input_path),
        "output_dir": str(output_path),
        "images": state.get("images", []),
        "vlm_cache_dir": str(vlm_cache.cache_dir),
        "completed_annotations": completed_annotations,
    }

    try:
        final_state = await app.ainvoke(
            workflow_input, config={"recursion_limit": 5000000}
        )
        processed = final_state.get("processed_count", 0)
        newly_completed = len(completed_annotations)
        logger.info(
            f"Batch {batch_idx} ({dataset_name}) offset={offset}: "
            f"{processed} new + {newly_completed} skipped = {processed + newly_completed} total"
        )
        return processed
    except Exception as e:
        logger.error(f"Batch {batch_idx} ({dataset_name}) offset={offset}: {e}")
        raise


async def process_dataset(input_path: Path, output_path: Path, dataset_name: str):
    logger.info(f"{'=' * 60}")
    logger.info(f"Starting dataset: {dataset_name}")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")

    image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
    all_images = sorted(
        [
            f
            for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
    )
    total_images = len(all_images)
    logger.info(f"Total images in {dataset_name}: {total_images}")

    if total_images == 0:
        logger.warning(f"No images found in {dataset_name}, skipping")
        return 0

    processed_images = get_processed_images(output_path, input_path)
    if processed_images:
        logger.info(
            f"Found {len(processed_images)} already-processed images, will skip"
        )

    vlm_cache = VLMCache(output_path / "vlm_cache")

    num_batches = (total_images + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(f"Splitting into {num_batches} batches of {BATCH_SIZE}")

    total_processed = 0
    batch_results = []

    for batch_idx in range(num_batches):
        offset = batch_idx * BATCH_SIZE

        batch_images = all_images[offset : offset + BATCH_SIZE]
        batch_image_paths = [str(p) for p in batch_images]

        remaining = [p for p in batch_image_paths if p not in processed_images]

        if remaining:
            logger.info(
                f"VLM prefetching {len(remaining)} images for batch {batch_idx + 1}..."
            )
            await vlm_cache.prefetch(remaining)
            logger.info(f"VLM prefetch complete for batch {batch_idx + 1}")

        completed_annotations = [
            {"image_path": img_path} for img_path in processed_images
        ]

        logger.info(f"Processing batch {batch_idx + 1}/{num_batches} (offset={offset})")

        try:
            processed = await process_batch(
                input_path,
                output_path,
                dataset_name,
                batch_idx,
                offset,
                completed_annotations,
                vlm_cache,
            )
            batch_results.append(processed)
            total_processed += processed
        except Exception as e:
            logger.error(f"Batch {batch_idx + 1} failed: {e}")
            batch_results.append(f"ERROR: {e}")

        for p in remaining:
            processed_images.add(p)

    logger.info(
        f"Completed {dataset_name}: {total_processed}/{total_images} images processed"
    )
    return total_processed


async def main():
    base_dir = Path("/data/lch/SAM/datasets/训练集/训练集")
    output_base = Path("/data/lch/SAM/datasets/训练集/annotated")

    datasets = ["data1", "data3", "data4", "data5", "data6", "data7"]

    logger.info(f"Starting batch processing of {len(datasets)} datasets")
    logger.info(f"Batch size: {BATCH_SIZE} images")
    logger.info(f"Log file: {log_file}")

    total_processed = 0
    results = {}

    for dataset in datasets:
        input_path = base_dir / dataset
        output_path = output_base / dataset

        if not input_path.exists():
            logger.warning(f"Dataset not found: {input_path}, skipping")
            continue

        output_path.mkdir(parents=True, exist_ok=True)

        try:
            processed = await process_dataset(input_path, output_path, dataset)
            results[dataset] = processed
            total_processed += processed
        except Exception as e:
            logger.error(f"Failed to process {dataset}: {e}")
            results[dataset] = f"ERROR: {e}"

    logger.info(f"{'=' * 60}")
    logger.info(f"Batch processing complete!")
    logger.info(f"Total images processed: {total_processed}")
    logger.info(f"Results: {results}")
    logger.info(f"Log file: {log_file}")


if __name__ == "__main__":
    asyncio.run(main())
