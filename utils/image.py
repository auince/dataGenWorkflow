"""Image loading and processing utilities."""

from typing import Tuple

import cv2
import numpy as np


def load_image(path: str) -> np.ndarray:
    """Load image from file path as numpy array.

    Args:
        path: Path to the image file

    Returns:
        Image as numpy array in BGR format (OpenCV default)
    """
    image = cv2.imread(path)
    if image is None:
        raise ValueError(f"Failed to load image from {path}")
    return image


def resize_image(image: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """Resize image to target size.

    Args:
        image: Input image as numpy array
        size: Target size as (width, height)

    Returns:
        Resized image
    """
    return cv2.resize(image, size, interpolation=cv2.INTER_LINEAR)
