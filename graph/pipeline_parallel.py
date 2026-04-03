"""Parallel pipeline for VLM-SAM continuous processing."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, "/data/lch/SAM/dataGenWorkflow")

from utils.logger import get_logger
from utils.pipeline_queue import AsyncPersistentQueue, PromptTask
from agents.vlm_worker import VLMWorkerPool, prefetch_vlm
from agents.sam_worker import SAMWorkerPool

logger = get_logger("pipeline_parallel")


class ParallelPipeline:
    def __init__(
        self,
        image_dir: str,
        output_dir: str,
        queue_dir: str,
        vlm_devices: list[str] = None,
        sam_device: str = "cuda:1",
        vlm_workers: int = 3,
        sam_workers: int = 2,
        batch_size: int = 100,
    ):
        self.image_dir = Path(image_dir)
        self.output_dir = Path(output_dir)
        self.queue_dir = Path(queue_dir)
        self.vlm_devices = vlm_devices or ["cuda:2", "cuda:3"]
        self.sam_device = sam_device
        self.vlm_workers = vlm_workers
        self.sam_workers = sam_workers
        self.batch_size = batch_size

        self.prompt_queue: AsyncPersistentQueue = None
        self.vlm_pool: VLMWorkerPool = None
        self.sam_pool: SAMWorkerPool = None

    async def setup(self):
        self.prompt_queue = AsyncPersistentQueue(
            str(self.queue_dir), name="prompt_queue"
        )
        self.vlm_pool = VLMWorkerPool(
            queue=self.prompt_queue,
            num_workers=self.vlm_workers,
            devices=self.vlm_devices,
        )
        self.sam_pool = SAMWorkerPool(
            prompt_queue=self.prompt_queue,
            output_dir=str(self.output_dir),
            num_workers=self.sam_workers,
            device=self.sam_device,
        )
        await self.vlm_pool.start()
        await self.sam_pool.start()
        logger.info("Pipeline setup complete")

    async def teardown(self):
        if self.vlm_pool:
            await self.vlm_pool.stop()
        if self.sam_pool:
            await self.sam_pool.stop()
        if self.prompt_queue:
            self.prompt_queue.close()
        logger.info("Pipeline teardown complete")

    async def process_images(self, image_paths: list[str]):
        await prefetch_vlm(self.prompt_queue, image_paths, batch_size=32)
        logger.info(f"Enqueued {len(image_paths)} images for VLM processing")

    async def run_until_complete(self, total_images: int = None):
        while True:
            stats = self.prompt_queue.get_stats()
            completed = stats["completed"]
            failed = stats["failed"]
            pending = stats["pending"]
            processing = stats["processing"]

            logger.info(
                f"Progress: {completed} completed, {failed} failed, "
                f"{pending} pending, {processing} processing"
            )

            if pending == 0 and processing == 0:
                if completed > 0 or failed > 0:
                    logger.info("All tasks processed")
                    break

            await asyncio.sleep(5)

        final_stats = self.prompt_queue.get_stats()
        return final_stats


async def run_pipeline(
    image_dir: str,
    output_dir: str,
    queue_dir: str,
    max_images: int = None,
    vlm_devices: list[str] = None,
    sam_device: str = "cuda:1",
    vlm_workers: int = 3,
    sam_workers: int = 2,
):
    pipeline = ParallelPipeline(
        image_dir=image_dir,
        output_dir=output_dir,
        queue_dir=queue_dir,
        vlm_devices=vlm_devices,
        sam_device=sam_device,
        vlm_workers=vlm_workers,
        sam_workers=sam_workers,
    )

    try:
        await pipeline.setup()

        image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
        all_images = sorted(
            [
                f
                for f in Path(image_dir).iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]
        )

        if max_images:
            all_images = all_images[:max_images]

        logger.info(f"Found {len(all_images)} images to process")

        image_paths = [str(p) for p in all_images]
        await pipeline.process_images(image_paths)

        final_stats = await pipeline.run_until_complete(len(all_images))

        logger.info(f"Pipeline complete: {final_stats}")
        return final_stats

    finally:
        await pipeline.teardown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parallel VLM-SAM Pipeline")
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--queue-dir", required=True)
    parser.add_argument("--max-images", type=int, default=None)
    parser.add_argument("--vlm-workers", type=int, default=3)
    parser.add_argument("--sam-workers", type=int, default=2)
    parser.add_argument("--sam-device", default="cuda:1")

    args = parser.parse_args()

    asyncio.run(
        run_pipeline(
            image_dir=args.image_dir,
            output_dir=args.output_dir,
            queue_dir=args.queue_dir,
            max_images=args.max_images,
            vlm_devices=["cuda:2", "cuda:3"],
            sam_device=args.sam_device,
            vlm_workers=args.vlm_workers,
            sam_workers=args.sam_workers,
        )
    )
