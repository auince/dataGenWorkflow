"""Checkpoint management for pipeline resumability.

Provides save/load functionality for PipelineState to enable
incremental processing and recovery from interruptions.
"""

import json
import os
import tempfile
import fcntl
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Set

from graph.types import AnnotationResult, CheckpointMetadata


class CheckpointError(Exception):
    """Base exception for checkpoint operations."""

    pass


class CheckpointLoadError(CheckpointError):
    """Raised when checkpoint file cannot be loaded."""

    pass


class CheckpointSaveError(CheckpointError):
    """Raised when checkpoint cannot be saved."""

    pass


class CheckpointState:
    """Serializable checkpoint state for pipeline resumability."""

    def __init__(
        self,
        total_images: int = 0,
        processed_count: int = 0,
        failed_count: int = 0,
        current_image: Optional[str] = None,
        current_image_results: Optional[list] = None,
        iteration_round: int = 0,
        low_quality_samples: Optional[list] = None,
        completed_annotations: Optional[list] = None,
        discarded_samples: Optional[list] = None,
        processed_images: Optional[Set[str]] = None,
        checkpoint_meta: Optional[dict] = None,
    ):
        self.total_images = total_images
        self.processed_count = processed_count
        self.failed_count = failed_count
        self.current_image = current_image
        self.current_image_results = current_image_results or []
        self.iteration_round = iteration_round
        self.low_quality_samples = low_quality_samples or []
        self.completed_annotations = completed_annotations or []
        self.discarded_samples = discarded_samples or []
        self.processed_images = processed_images or set()
        self.checkpoint_meta = checkpoint_meta or {"step": 0, "timestamp": ""}

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_images": self.total_images,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "current_image": self.current_image,
            "current_image_results": self.current_image_results,
            "iteration_round": self.iteration_round,
            "low_quality_samples": self.low_quality_samples,
            "completed_annotations": self.completed_annotations,
            "discarded_samples": self.discarded_samples,
            "processed_images": list(self.processed_images),
            "checkpoint_meta": self.checkpoint_meta,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CheckpointState":
        """Create CheckpointState from dictionary."""
        state = cls(
            total_images=data.get("total_images", 0),
            processed_count=data.get("processed_count", 0),
            failed_count=data.get("failed_count", 0),
            current_image=data.get("current_image"),
            current_image_results=data.get("current_image_results", []),
            iteration_round=data.get("iteration_round", 0),
            low_quality_samples=data.get("low_quality_samples", []),
            completed_annotations=data.get("completed_annotations", []),
            discarded_samples=data.get("discarded_samples", []),
            processed_images=set(data.get("processed_images", [])),
            checkpoint_meta=data.get("checkpoint_meta", {"step": 0, "timestamp": ""}),
        )
        return state

    @classmethod
    def from_pipeline_state(cls, state: dict) -> "CheckpointState":
        """Create CheckpointState from PipelineState dict."""
        checkpoint_meta = state.get("checkpoint", {"step": 0, "timestamp": ""})
        if isinstance(checkpoint_meta, dict):
            checkpoint_meta = {
                "step": checkpoint_meta.get("step", 0),
                "timestamp": checkpoint_meta.get("timestamp", ""),
                "agent_name": checkpoint_meta.get("agent_name"),
            }

        return cls(
            total_images=state.get("total_images", 0),
            processed_count=state.get("processed_count", 0),
            failed_count=state.get("failed_count", 0),
            current_image=state.get("current_image"),
            current_image_results=state.get("current_image_results", []),
            iteration_round=state.get("iteration_round", 0),
            low_quality_samples=state.get("low_quality_samples", []),
            completed_annotations=state.get("completed_annotations", []),
            discarded_samples=state.get("discarded_samples", []),
            processed_images=set(),
            checkpoint_meta=checkpoint_meta,
        )

    def to_pipeline_state(self) -> dict:
        """Convert back to PipelineState dict format."""
        return {
            "total_images": self.total_images,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "current_image": self.current_image,
            "current_image_results": self.current_image_results,
            "iteration_round": self.iteration_round,
            "low_quality_samples": self.low_quality_samples,
            "completed_annotations": self.completed_annotations,
            "discarded_samples": self.discarded_samples,
            "checkpoint": CheckpointMetadata(
                step=self.checkpoint_meta.get("step", 0),
                timestamp=self.checkpoint_meta.get("timestamp", ""),
                agent_name=self.checkpoint_meta.get("agent_name"),
            ),
        }

    def is_image_processed(self, image_path: str) -> bool:
        """Check if an image has already been processed."""
        return image_path in self.processed_images

    def mark_image_processed(self, image_path: str) -> None:
        """Mark an image as processed."""
        self.processed_images.add(image_path)


def _atomic_write_json(filepath: str, data: dict) -> None:
    """Atomically write JSON data to file using temp file + rename."""
    path_obj = Path(filepath)
    dir_path = path_obj.parent

    dir_path.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=dir_path,
        prefix=".checkpoint_tmp_",
        suffix=".json",
        delete=False,
    ) as f:
        temp_path = f.name
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())

    os.replace(temp_path, str(path_obj))


def _read_json_safe(filepath: str) -> Optional[dict]:
    """Safely read JSON file, returns None if invalid."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


@contextmanager
def _file_lock(filepath: str, exclusive: bool = True):
    """Context manager for file locking (thread-safe operations)."""
    lock_path = Path(filepath).with_suffix(".lock")
    with open(lock_path, "w") as lock_file:
        lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(lock_file.fileno(), lock_type)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def save_checkpoint(path: str, state: dict) -> None:
    """Save PipelineState to checkpoint file.

    Args:
        path: Path to checkpoint JSON file
        state: PipelineState dictionary to save

    Raises:
        CheckpointSaveError: If checkpoint cannot be saved
    """
    try:
        checkpoint_state = CheckpointState.from_pipeline_state(state)

        checkpoint_state.checkpoint_meta = {
            "step": state.get("checkpoint", {}).get("step", 0) + 1,
            "timestamp": state.get("checkpoint", {}).get("timestamp", "")
            or time.strftime("%Y-%m-%dT%H:%M:%S"),
            "agent_name": state.get("checkpoint", {}).get("agent_name"),
        }

        with _file_lock(path, exclusive=True):
            _atomic_write_json(path, checkpoint_state.to_dict())

    except Exception as e:
        raise CheckpointSaveError(f"Failed to save checkpoint: {e}") from e


def load_checkpoint(path: str) -> Optional[dict]:
    """Load checkpoint and return state dict.

    Args:
        path: Path to checkpoint JSON file

    Returns:
        PipelineState dict if checkpoint exists and is valid, None otherwise
    """
    checkpoint_path = Path(path)

    if not checkpoint_path.exists():
        return None

    with _file_lock(path, exclusive=False):
        data = _read_json_safe(path)

    if data is None:
        return None

    try:
        checkpoint_state = CheckpointState.from_dict(data)
        return checkpoint_state.to_pipeline_state()
    except (KeyError, TypeError) as e:
        return None


def is_processed(path: str, image_path: str) -> bool:
    """Check if an image is marked as processed in checkpoint.

    Args:
        path: Path to checkpoint file
        image_path: Path to image to check

    Returns:
        True if image is in processed set, False otherwise
    """
    checkpoint_path = Path(path)

    if not checkpoint_path.exists():
        return False

    with _file_lock(path, exclusive=False):
        data = _read_json_safe(path)

    if data is None:
        return False

    processed_images = data.get("processed_images", [])
    return image_path in processed_images


def mark_processed(path: str, image_path: str) -> None:
    """Mark an image as processed in checkpoint.

    Args:
        path: Path to checkpoint file
        image_path: Path to image to mark as processed
    """
    with _file_lock(path, exclusive=True):
        data = _read_json_safe(path) or {"processed_images": []}
        if "processed_images" not in data:
            data["processed_images"] = []
        if image_path not in data["processed_images"]:
            data["processed_images"].append(image_path)
        _atomic_write_json(path, data)
