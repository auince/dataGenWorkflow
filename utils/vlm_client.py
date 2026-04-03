"""VLM (Vision Language Model) client for Qwen3-VL-32B."""

import base64
import os
from pathlib import Path
from typing import Union

from openai import OpenAI

from utils.logger import get_logger

BASE_URL = "http://localhost:1285/v1"
API_KEY = "EMPTY"
MODEL = "Qwen/Qwen3-VL-32B-Instruct"
TIMEOUT = 60.0

_logger = get_logger(__name__)

_vlm_client: OpenAI | None = None


def get_vlm_client() -> OpenAI:
    """Get singleton VLM client instance.

    Returns:
        OpenAI client configured for Qwen3-VL-32B
    """
    global _vlm_client
    if _vlm_client is None:
        _vlm_client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
            timeout=TIMEOUT,
        )
    return _vlm_client


def _encode_image_to_base64(image_path: str) -> str:
    """Encode image file to base64 string.

    Args:
        image_path: Path to the image file

    Returns:
        Base64 encoded image string (without data URL prefix)
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _build_content(image: Union[str, bytes], prompt: str) -> list[dict]:
    """Build message content for VLM request.

    Args:
        image: Image as file path (str), base64 string, or bytes
        prompt: Text prompt to send with the image

    Returns:
        Content list for chat completion messages
    """
    content: list[dict] = []

    if isinstance(image, bytes):
        # Bytes input - encode to base64
        b64_image = base64.b64encode(image).decode("utf-8")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
            }
        )
    elif isinstance(image, str):
        if image.startswith("data:"):
            # Already a data URL
            content.append({"type": "image_url", "image_url": {"url": image}})
        elif os.path.exists(image):
            # Local file path - check if it exists
            if (
                image.startswith("file://")
                or os.path.isabs(image)
                or os.path.isfile(image)
            ):
                # Use file:// URL format for local files
                file_path = image.removeprefix("file://")
                content.append(
                    {"type": "image_url", "image_url": {"url": f"file://{file_path}"}}
                )
            else:
                # Path without file:// prefix
                content.append(
                    {"type": "image_url", "image_url": {"url": f"file://{image}"}}
                )
        elif image.startswith("http://") or image.startswith("https://"):
            # HTTP URL
            content.append({"type": "image_url", "image_url": {"url": image}})
        else:
            # Assume it's a base64 string without prefix
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                }
            )
    else:
        raise TypeError(f"Unsupported image type: {type(image)}")

    content.append({"type": "text", "text": prompt})
    return content


def call_vlm(image: Union[str, bytes], prompt: str, max_tokens: int = 512) -> str:
    """Call VLM with image and text prompt.

    Args:
        image: Image as file path, URL, base64 string, or bytes
        prompt: Text prompt to send with the image
        max_tokens: Maximum tokens in response (default: 512)

    Returns:
        VLM response text

    Raises:
        OpenAIError: If the API call fails
        ValueError: If image cannot be processed
    """
    client = get_vlm_client()
    content = _build_content(image, prompt)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        _logger.error(f"VLM call failed: {e}")
        raise
