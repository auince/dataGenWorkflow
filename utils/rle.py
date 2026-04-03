"""RLE encode/decode utilities using pycocotools."""

from typing import Any, Tuple

import numpy as np
from pycocotools import mask as coco_mask


def encode_mask(mask: np.ndarray) -> Any:
    """Encode binary mask to COCO RLE format."""
    mask = mask.astype(np.uint8)
    rle = coco_mask.encode(np.asfortranarray(mask))
    return rle


def decode_mask(rle: Any, size: Tuple[int, int]) -> np.ndarray:
    """Decode COCO RLE format to binary mask."""
    mask = coco_mask.decode(rle)
    return mask
