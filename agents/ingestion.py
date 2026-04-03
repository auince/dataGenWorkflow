"""IngestionAgent for loading, converting, deduplicating, and quality-checking images."""

import hashlib
from pathlib import Path
from typing import List, Set, TypedDict

import cv2
import numpy as np

from agents.base import BaseAgent
from tools.base import BaseTool
from utils.logger import get_logger


class ImageMetadata(TypedDict):
    """Metadata for an ingested image."""

    path: str
    hash: str
    width: int
    height: int
    format: str


class IngestionState(TypedDict):
    """State schema for the ingestion pipeline."""

    image_dir: str
    images: List[ImageMetadata]
    total_found: int
    duplicates_removed: int
    low_quality_removed: int
    errors: List[str]


class LoadImagesInput(BaseTool):
    """Input schema for loading images."""

    directory: str


class LoadImagesTool(BaseTool):
    """Tool for loading images from a directory."""

    name: str = "load_images"
    description: str = "Load all valid images from a directory"

    def _run(self, directory: str) -> List[str]:
        """Load image paths from directory.

        Args:
            directory: Path to directory containing images

        Returns:
            List of valid image file paths
        """
        supported_formats = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
        image_paths = []

        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory not found: {directory}")

        for ext in supported_formats:
            image_paths.extend(dir_path.rglob(f"*{ext}"))
            image_paths.extend(dir_path.rglob(f"*{ext.upper()}"))

        return [str(p) for p in image_paths]


class ConvertFormatInput(BaseTool):
    """Input schema for format conversion."""

    image_path: str
    target_format: str


class ConvertFormatTool(BaseTool):
    """Tool for converting image formats."""

    name: str = "convert_format"
    description: str = "Convert image to target format"

    def _run(self, image_path: str, target_format: str = "png") -> str:
        """Convert image to target format.

        Args:
            image_path: Path to source image
            target_format: Target format (e.g., 'png', 'jpg')

        Returns:
            Path to converted image
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")

        base_path = Path(image_path)
        output_path = base_path.with_suffix(f".{target_format}")
        cv2.imwrite(str(output_path), img)

        return str(output_path)


class DeduplicateImagesInput(BaseTool):
    """Input schema for deduplication."""

    image_paths: List[str]


class DeduplicateImagesTool(BaseTool):
    """Tool for deduplicating images based on content hash."""

    name: str = "deduplicate_images"
    description: str = "Remove duplicate images based on content hash"

    def _run(self, image_paths: List[str]) -> List[str]:
        """Find and remove duplicate images.

        Args:
            image_paths: List of image paths to check

        Returns:
            List of unique image paths (duplicates removed)
        """
        seen_hashes: Set[str] = set()
        unique_paths: List[str] = []

        for path in image_paths:
            img = cv2.imread(path)
            if img is None:
                continue

            # Compute hash of image content
            img_hash = hashlib.md5(img.tobytes()).hexdigest()

            if img_hash not in seen_hashes:
                seen_hashes.add(img_hash)
                unique_paths.append(path)

        return unique_paths


class QualityCheckInput(BaseTool):
    """Input schema for quality check."""

    image_path: str


class QualityCheckTool(BaseTool):
    """Tool for checking image quality."""

    name: str = "quality_check"
    description: str = "Check if image meets quality thresholds"

    def __init__(
        self,
        min_width: int = 256,
        min_height: int = 256,
        min_quality: int = 30,
    ):
        """Initialize quality check tool.

        Args:
            min_width: Minimum image width
            min_height: Minimum image height
            min_quality: Minimum JPEG quality score (0-100)
        """
        super().__init__()
        self.min_width = min_width
        self.min_height = min_height
        self.min_quality = min_quality

    def _run(self, image_path: str) -> bool:
        """Check if image meets quality criteria.

        Args:
            image_path: Path to image to check

        Returns:
            True if image passes quality check, False otherwise
        """
        img = cv2.imread(image_path)
        if img is None:
            return False

        height, width = img.shape[:2]

        # Check resolution
        if width < self.min_width or height < self.min_height:
            return False

        # Check if image is not too dark or too bright
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)

        if mean_brightness < 10 or mean_brightness > 245:
            return False

        # Check contrast
        contrast = np.std(gray)
        if contrast < 10:
            return False

        return True


class IngestionAgent(BaseAgent[IngestionState]):
    """Agent for ingesting and processing images.

    Handles image loading, format normalization, deduplication,
    and quality filtering for the annotation pipeline.
    """

    def __init__(
        self,
        name: str = "ingestion",
        min_width: int = 256,
        min_height: int = 256,
        min_quality: int = 30,
        skip_deduplication: bool = False,
        skip_quality_check: bool = True,
    ):
        """Initialize IngestionAgent.

        Args:
            name: Agent name
            min_width: Minimum image width for quality check
            min_height: Minimum image height for quality check
            min_quality: Minimum quality score for images
            skip_deduplication: Skip deduplication step if True
            skip_quality_check: Skip quality check step if True (default True, do quality check per-image in pipeline)
        """
        super().__init__(name)
        self.logger = get_logger(f"agents.{name}")
        self.skip_deduplication = skip_deduplication
        self.skip_quality_check = skip_quality_check

        self.load_images_tool = LoadImagesTool()
        self.deduplicate_tool = DeduplicateImagesTool()
        self.quality_check_tool = QualityCheckTool(
            min_width=min_width,
            min_height=min_height,
            min_quality=min_quality,
        )

    async def process(self, state: IngestionState) -> IngestionState:
        """Process images from directory through ingestion pipeline.

        Args:
            state: Current pipeline state with image_dir

        Returns:
            Updated state with processed image metadata
        """
        self.logger.info(f"Starting ingestion from: {state['image_dir']}")

        # Load images
        image_paths = self.load_images_tool.run(directory=state["image_dir"])
        state["total_found"] = len(image_paths)
        self.logger.info(f"Found {len(image_paths)} images")

        if self.skip_deduplication:
            unique_paths = image_paths
            state["duplicates_removed"] = 0
            self.logger.info(f"Skipped deduplication, {len(unique_paths)} images")
        else:
            unique_paths = self.deduplicate_tool.run(image_paths=image_paths)
            state["duplicates_removed"] = len(image_paths) - len(unique_paths)
            self.logger.info(
                f"Removed {state['duplicates_removed']} duplicates, "
                f"{len(unique_paths)} unique images"
            )

        if self.skip_quality_check:
            passed_images: List[ImageMetadata] = []
            for path in unique_paths:
                img = cv2.imread(path)
                if img is not None:
                    height, width = img.shape[:2]
                    img_hash = hashlib.md5(img.tobytes()).hexdigest()
                    passed_images.append(
                        ImageMetadata(
                            path=path,
                            hash=img_hash,
                            width=width,
                            height=height,
                            format=Path(path).suffix.lstrip("."),
                        )
                    )
            state["images"] = passed_images
            self.logger.info(
                f"Skipped quality check, {len(passed_images)} images added for pipeline processing"
            )
        else:
            passed_images: List[ImageMetadata] = []
            for path in unique_paths:
                if self.quality_check_tool.run(image_path=path):
                    img = cv2.imread(path)
                    if img is not None:
                        height, width = img.shape[:2]
                        img_hash = hashlib.md5(img.tobytes()).hexdigest()
                        passed_images.append(
                            ImageMetadata(
                                path=path,
                                hash=img_hash,
                                width=width,
                                height=height,
                                format=Path(path).suffix.lstrip("."),
                            )
                        )
                else:
                    state["low_quality_removed"] += 1

            state["images"] = passed_images
            self.logger.info(
                f"Quality check passed: {len(passed_images)} images, "
                f"removed {state['low_quality_removed']} low quality"
            )

        return state
