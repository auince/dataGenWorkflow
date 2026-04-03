"""MiniMax API client for MiniMax-M2.7 model."""

import os
from pathlib import Path
from typing import Any, Iterator

from openai import OpenAI

from utils.logger import get_logger

BASE_URL = "https://api.minimaxi.com/v1"
MODEL = "MiniMax-M2.7"
TIMEOUT = 60.0

_logger = get_logger(__name__)

_minimax_client: OpenAI | None = None


def _get_api_key() -> str:
    """Get API key from environment variable or config file.

    Returns:
        API key string

    Raises:
        ValueError: If API key is not found
    """
    # Try environment variable first
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key

    # Try config file
    config_path = Path(__file__).parent.parent / "ApiDoc" / "minimax_apikey.txt"
    if config_path.exists():
        api_key = config_path.read_text().strip()
        if api_key:
            return api_key

    raise ValueError(
        "MiniMax API key not found. Set OPENAI_API_KEY environment variable "
        "or create ApiDoc/minimax_apikey.txt"
    )


def get_minimax_client() -> OpenAI:
    """Get singleton MiniMax client instance.

    Returns:
        OpenAI client configured for MiniMax API
    """
    global _minimax_client
    if _minimax_client is None:
        _minimax_client = OpenAI(
            api_key=_get_api_key(),
            base_url=BASE_URL,
            timeout=TIMEOUT,
        )
    return _minimax_client


def chat(
    messages: list[dict[str, Any]],
    max_tokens: int = 512,
    reasoning_split: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Send a chat completion request to MiniMax.

    Args:
        messages: List of message dicts with 'role' and 'content'
        max_tokens: Maximum tokens in response (default: 512)
        reasoning_split: Whether to split reasoning into separate field (default: False)
        **kwargs: Additional arguments to pass to the API

    Returns:
        Response dict with 'content' and optionally 'reasoning_details'

    Raises:
        OpenAIError: If the API call fails
    """
    client = get_minimax_client()

    extra_body = kwargs.pop("extra_body", {})
    if reasoning_split:
        extra_body["reasoning_split"] = True

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=max_tokens,
            extra_body=extra_body if extra_body else None,
            **kwargs,
        )

        result: dict[str, Any] = {
            "content": response.choices[0].message.content,
        }

        # Extract reasoning details if available
        if hasattr(response.choices[0].message, "reasoning_details"):
            result["reasoning_details"] = response.choices[0].message.reasoning_details

        return result
    except Exception as e:
        _logger.error(f"MiniMax chat call failed: {e}")
        raise


def stream(
    messages: list[dict[str, Any]],
    max_tokens: int = 512,
    reasoning_split: bool = True,
    **kwargs: Any,
) -> Iterator[dict[str, Any]]:
    """Stream a chat completion response from MiniMax with reasoning separation.

    Args:
        messages: List of message dicts with 'role' and 'content'
        max_tokens: Maximum tokens in response (default: 512)
        reasoning_split: Whether to split reasoning into separate field (default: True)
        **kwargs: Additional arguments to pass to the API

    Yields:
        Dicts with 'type' ('reasoning' or 'content'), 'text', and optional 'done'

    Raises:
        OpenAIError: If the API call fails
    """
    client = get_minimax_client()

    extra_body = kwargs.pop("extra_body", {})
    if reasoning_split:
        extra_body["reasoning_split"] = True

    try:
        stream_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=max_tokens,
            extra_body=extra_body if extra_body else None,
            stream=True,
            **kwargs,
        )

        reasoning_buffer = ""
        text_buffer = ""

        for chunk in stream_response:
            delta = chunk.choices[0].delta

            # Handle reasoning details
            if (
                reasoning_split
                and hasattr(delta, "reasoning_details")
                and delta.reasoning_details
            ):
                for detail in delta.reasoning_details:
                    if "text" in detail:
                        reasoning_text = detail["text"]
                        new_reasoning = reasoning_text[len(reasoning_buffer) :]
                        if new_reasoning:
                            yield {
                                "type": "reasoning",
                                "text": new_reasoning,
                            }
                            reasoning_buffer = reasoning_text

            # Handle content
            if delta.content:
                content_text = delta.content
                new_text = (
                    content_text[len(text_buffer) :] if text_buffer else content_text
                )
                if new_text:
                    yield {
                        "type": "content",
                        "text": new_text,
                    }
                    text_buffer = content_text

        # Signal completion
        yield {"type": "done", "reasoning": reasoning_buffer, "content": text_buffer}

    except Exception as e:
        _logger.error(f"MiniMax stream call failed: {e}")
        raise
