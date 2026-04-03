#!/usr/bin/env python3
import asyncio
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

sys.path.insert(0, "/data/lch/SAM/dataGenAgent")

from graph.pipeline import create_workflow
from main import initialize_state

BATCH_SIZE = 100


async def process_batch(
    input_path: Path,
    output_path: Path,
    dataset_name: str,
    batch_idx: int,
    offset: int,
):
    app = create_workflow()
    state = initialize_state(
        input_path, max_images=BATCH_SIZE, checkpoint_data=None, offset=offset
    )
    state["output_dir"] = str(output_path)

    workflow_input = {
        "image_dir": str(input_path),
        "output_dir": str(output_path),
        "images": state.get("images", []),
    }

    try:
        final_state = await app.ainvoke(
            workflow_input, config={"recursion_limit": 5000000}
        )
        processed = final_state.get("processed_count", 0)
        logger.info(
            f"Batch {batch_idx} ({dataset_name}) offset={offset}: {processed} images processed"
        )
        return processed
    except Exception as e:
        logger.error(f"Batch {batch_idx} ({dataset_name}) offset={offset}: {e}")
        raise


async def process_dataset(input_path: Path, output_path: Path, dataset_name: str):
    logger.info(f"=" * 60)
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

    num_batches = (total_images + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(f"Splitting into {num_batches} batches of {BATCH_SIZE}")

    total_processed = 0
    batch_results = []

    for batch_idx in range(num_batches):
        offset = batch_idx * BATCH_SIZE
        logger.info(f"Processing batch {batch_idx + 1}/{num_batches} (offset={offset})")

        try:
            processed = await process_batch(
                input_path, output_path, dataset_name, batch_idx, offset
            )
            batch_results.append(processed)
            total_processed += processed
        except Exception as e:
            logger.error(f"Batch {batch_idx + 1} failed: {e}")
            batch_results.append(f"ERROR: {e}")

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
