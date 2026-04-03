#!/usr/bin/env python3
"""CLI entry point for the multi-agent data generation pipeline.

Usage:
    python main.py --input /path/to/images --output /path/to/output
    python main.py --input /path/to/images --output /path/to/output --max-images 100
    python main.py --input /path/to/images --output /path/to/output --checkpoint /path/to/checkpoint.json
    python main.py --input /path/to/images --output /path/to/output --verbose
"""

import argparse
import asyncio
import sys
from pathlib import Path

import cv2
from tqdm import tqdm

from utils.logger import get_logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Multi-Agent Data Generation Pipeline - Generate pseudo-labels using SAM3 and VLM evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input ./images --output ./output
  %(prog)s --input ./images --output ./output --max-images 100
  %(prog)s --input ./images --output ./output --checkpoint checkpoint.json
  %(prog)s --input ./images --output ./output --verbose
        """,
    )

    # Required arguments
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        type=str,
        metavar="DIR",
        help="Input directory containing images to process",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        type=str,
        metavar="DIR",
        help="Output directory for generated pseudo-labels",
    )

    # Optional arguments
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of images to process (default: all images)",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to checkpoint file for resuming interrupted processing",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (INFO level)",
    )

    return parser.parse_args()


def validate_input_directory(input_path: Path) -> None:
    """Validate that input directory exists and contains images.

    Args:
        input_path: Path to input directory

    Raises:
        FileNotFoundError: If input directory does not exist
        ValueError: If input directory is empty or contains no images
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_path}")

    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_path}")

    # Check for image files
    image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
    image_files = [
        f
        for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if not image_files:
        raise ValueError(f"No image files found in {input_path}")


def ensure_output_directory(output_path: Path) -> None:
    """Create output directory if it doesn't exist.

    Args:
        output_path: Path to output directory
    """
    output_path.mkdir(parents=True, exist_ok=True)


def initialize_state(
    input_path: Path,
    max_images: int | None,
    checkpoint_data: dict | None,
    offset: int = 0,
) -> "PipelineState":
    """Initialize pipeline state.

    Args:
        input_path: Path to input directory
        max_images: Maximum number of images to process
        checkpoint_data: Loaded checkpoint data if resuming
        offset: Number of images to skip from the beginning (for batching)

    Returns:
        Initialized pipeline state
    """
    from graph.state import PipelineState
    from graph.types import CheckpointMetadata

    image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
    all_images = sorted(
        [
            f
            for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
    )

    # Apply offset and limit
    if offset > 0:
        all_images = all_images[offset:]
    if max_images is not None and len(all_images) > max_images:
        all_images = all_images[:max_images]

    total_images = len(all_images)

    if max_images is not None and total_images > 0:
        import hashlib

        pre_populated_images = []
        for img_path in all_images:
            img = cv2.imread(str(img_path))
            if img is not None:
                height, width = img.shape[:2]
                img_hash = hashlib.md5(img.tobytes()).hexdigest()
                pre_populated_images.append(
                    {
                        "path": str(img_path),
                        "hash": img_hash,
                        "width": width,
                        "height": height,
                        "format": img_path.suffix.lstrip("."),
                    }
                )
        images_to_use = pre_populated_images
    else:
        images_to_use = []

    if checkpoint_data:
        # Resume from checkpoint
        state = checkpoint_data.get("state", {})
        state["checkpoint"] = CheckpointMetadata(
            step=state.get("processed_count", 0),
            timestamp=checkpoint_data.get("timestamp", ""),
            agent_name="resumed",
        )
        return state

    # Fresh start
    return PipelineState(
        total_images=total_images,
        processed_count=0,
        failed_count=0,
        current_image=None,
        current_image_results=[],
        iteration_round=0,
        low_quality_samples=[],
        completed_annotations=[],
        discarded_samples=[],
        checkpoint=CheckpointMetadata(step=0, timestamp="", agent_name=None),
        image_dir=str(input_path),
        images=images_to_use,
    )


async def run_pipeline(
    state: "PipelineState", input_path: Path, output_path: Path, verbose: bool = False
) -> "PipelineState":
    """Run the multi-agent pipeline.

    Args:
        state: Initial pipeline state
        input_path: Path to input directory
        output_path: Path to output directory
        verbose: Enable verbose logging

    Returns:
        Final pipeline state after processing
    """
    from graph.pipeline import create_workflow

    logger = get_logger(__name__)

    # Create workflow
    app = create_workflow()

    # Prepare initial input for workflow
    workflow_input = {
        "image_dir": str(input_path),
        "output_dir": str(output_path),
        "max_images": state.get("total_images", 0),
        "resume": state.get("processed_count", 0) > 0,
    }

    if state.get("images"):
        workflow_input["images"] = state["images"]

    # Create progress bar
    total = state.get("total_images", 0)
    with tqdm(total=total, desc="Processing images", unit="img") as pbar:
        pbar.update(state.get("processed_count", 0))

        # Invoke workflow with progress updates
        try:
            final_state = await app.ainvoke(
                workflow_input, config={"recursion_limit": 1000}
            )

            # Update progress bar to completion
            pbar.update(final_state.get("total_images", 0) - pbar.n)

            return final_state

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise


def save_state_checkpoint(
    state: "PipelineState", checkpoint_path: Path, logger: "logging.Logger"
) -> None:
    """Save pipeline state checkpoint.

    Args:
        state: Current pipeline state
        checkpoint_path: Path to save checkpoint
        logger: Logger instance
    """
    import json
    from datetime import datetime

    checkpoint_data = {"state": dict(state), "timestamp": datetime.now().isoformat()}

    try:
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f, indent=2)
        logger.info(f"Checkpoint saved to {checkpoint_path}")
    except Exception as e:
        logger.warning(f"Failed to save checkpoint: {e}")


def main() -> int:
    """Main entry point for CLI.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    args = parse_args()

    # Setup logger
    logger = get_logger(__name__)
    if args.verbose:
        import logging

        logger.setLevel(logging.DEBUG)

    # Convert paths
    input_path = Path(args.input)
    output_path = Path(args.output)

    # Validate input directory
    try:
        validate_input_directory(input_path)
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        logger.error(f"Input validation failed: {e}")
        return 1

    # Create output directory if needed
    ensure_output_directory(output_path)

    # Load checkpoint if provided
    checkpoint_data = None
    if args.checkpoint:
        from utils.checkpoint import load_checkpoint

        checkpoint_path = Path(args.checkpoint)
        if checkpoint_path.exists():
            try:
                checkpoint_data = load_checkpoint(str(checkpoint_path))
                logger.info(f"Loaded checkpoint from {checkpoint_path}")
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
                checkpoint_data = None
        else:
            logger.warning(f"Checkpoint file not found: {checkpoint_path}")

    # Initialize state
    try:
        state = initialize_state(input_path, args.max_images, checkpoint_data)
        logger.info(f"Processing {state['total_images']} images")
    except Exception as e:
        logger.error(f"Failed to initialize state: {e}")
        return 1

    # Run pipeline
    try:
        final_state = asyncio.run(
            run_pipeline(state, input_path, output_path, args.verbose)
        )

        # Report results
        processed = final_state.get("processed_count", 0)
        failed = final_state.get("failed_count", 0)
        completed = len(final_state.get("completed_annotations", []))

        logger.info(
            f"Processing complete: {processed} processed, {failed} failed, {completed} completed"
        )

        # Save final checkpoint
        if args.checkpoint:
            checkpoint_path = Path(args.checkpoint)
            save_state_checkpoint(final_state, checkpoint_path, logger)

        return 0

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")

        # Save checkpoint on interrupt
        if args.checkpoint:
            checkpoint_path = Path(args.checkpoint)
            save_state_checkpoint(state, checkpoint_path, logger)
            logger.info(f"State saved to checkpoint for resume")

        return 130

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()

        # Save checkpoint on error
        if args.checkpoint:
            checkpoint_path = Path(args.checkpoint)
            save_state_checkpoint(state, checkpoint_path, logger)

        return 1


if __name__ == "__main__":
    sys.exit(main())
