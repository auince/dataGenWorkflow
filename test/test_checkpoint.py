"""Unit tests for checkpoint functionality."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.checkpoint import (
    CheckpointState,
    save_checkpoint,
    load_checkpoint,
    is_processed,
    mark_processed,
    CheckpointLoadError,
    CheckpointSaveError,
)


class TestCheckpointState(TestCase):
    """Tests for CheckpointState class."""

    def test_create_checkpoint_state(self):
        """Test creating a CheckpointState."""
        state = CheckpointState(
            total_images=10,
            processed_count=5,
            failed_count=1,
            current_image="/path/to/image.png",
            iteration_round=2,
        )

        self.assertEqual(state.total_images, 10)
        self.assertEqual(state.processed_count, 5)
        self.assertEqual(state.failed_count, 1)
        self.assertEqual(state.current_image, "/path/to/image.png")
        self.assertEqual(state.iteration_round, 2)

    def test_to_dict(self):
        """Test converting CheckpointState to dictionary."""
        state = CheckpointState(
            total_images=10,
            processed_count=5,
            processed_images={"/path/to/image1.png", "/path/to/image2.png"},
        )

        d = state.to_dict()
        self.assertEqual(d["total_images"], 10)
        self.assertEqual(d["processed_count"], 5)
        self.assertIn("/path/to/image1.png", d["processed_images"])

    def test_from_dict(self):
        """Test creating CheckpointState from dictionary."""
        data = {
            "total_images": 10,
            "processed_count": 5,
            "processed_images": ["/path/to/image1.png"],
            "checkpoint_meta": {"step": 3, "timestamp": "2024-01-01T12:00:00"},
        }

        state = CheckpointState.from_dict(data)
        self.assertEqual(state.total_images, 10)
        self.assertEqual(state.processed_count, 5)
        self.assertIn("/path/to/image1.png", state.processed_images)

    def test_from_pipeline_state(self):
        """Test creating CheckpointState from PipelineState."""
        pipeline_state = {
            "total_images": 10,
            "processed_count": 3,
            "failed_count": 2,
            "current_image": "/path/to/image.png",
            "current_image_results": [],
            "iteration_round": 1,
            "low_quality_samples": [],
            "completed_annotations": [],
            "discarded_samples": [],
            "checkpoint": {
                "step": 5,
                "timestamp": "2024-01-01T12:00:00",
                "agent_name": "validation",
            },
        }

        state = CheckpointState.from_pipeline_state(pipeline_state)
        self.assertEqual(state.total_images, 10)
        self.assertEqual(state.processed_count, 3)
        self.assertEqual(state.checkpoint_meta["step"], 5)

    def test_is_image_processed(self):
        """Test checking if image is processed."""
        state = CheckpointState(processed_images={"/path/to/image1.png"})
        self.assertTrue(state.is_image_processed("/path/to/image1.png"))
        self.assertFalse(state.is_image_processed("/path/to/image2.png"))

    def test_mark_image_processed(self):
        """Test marking an image as processed."""
        state = CheckpointState()
        state.mark_image_processed("/path/to/image.png")
        self.assertTrue(state.is_image_processed("/path/to/image.png"))


class TestCheckpointSaveLoad(TestCase):
    """Tests for checkpoint save and load functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoint_path = os.path.join(self.test_dir, "checkpoint.json")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_and_load_checkpoint(self):
        """Test saving and loading a checkpoint."""
        state = {
            "total_images": 10,
            "processed_count": 5,
            "failed_count": 1,
            "current_image": "/path/to/image.png",
            "current_image_results": [],
            "iteration_round": 2,
            "low_quality_samples": [],
            "completed_annotations": [],
            "discarded_samples": [],
            "checkpoint": {
                "step": 3,
                "timestamp": "2024-01-01T12:00:00",
                "agent_name": "test",
            },
        }

        save_checkpoint(self.checkpoint_path, state)
        self.assertTrue(os.path.exists(self.checkpoint_path))

        loaded = load_checkpoint(self.checkpoint_path)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["processed_count"], 5)
        self.assertEqual(loaded["failed_count"], 1)

    def test_load_nonexistent_checkpoint(self):
        """Test loading a checkpoint that doesn't exist."""
        result = load_checkpoint("/nonexistent/path/checkpoint.json")
        self.assertIsNone(result)

    def test_save_checkpoint_with_existing_directory(self):
        """Test saving checkpoint when parent directory exists."""
        state = {"total_images": 10, "processed_count": 0}
        save_checkpoint(self.checkpoint_path, state)
        self.assertTrue(os.path.exists(self.checkpoint_path))


class TestIsProcessedMarkProcessed(TestCase):
    """Tests for is_processed and mark_processed functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoint_path = os.path.join(self.test_dir, "checkpoint.json")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_is_processed(self):
        """Test is_processed function."""
        self.assertFalse(is_processed(self.checkpoint_path, "/path/to/image.png"))

        mark_processed(self.checkpoint_path, "/path/to/image.png")
        self.assertTrue(is_processed(self.checkpoint_path, "/path/to/image.png"))

    def test_mark_processed_multiple(self):
        """Test marking multiple images as processed."""
        mark_processed(self.checkpoint_path, "/path/to/image1.png")
        mark_processed(self.checkpoint_path, "/path/to/image2.png")

        self.assertTrue(is_processed(self.checkpoint_path, "/path/to/image1.png"))
        self.assertTrue(is_processed(self.checkpoint_path, "/path/to/image2.png"))
        self.assertFalse(is_processed(self.checkpoint_path, "/path/to/image3.png"))


if __name__ == "__main__":
    import unittest

    unittest.main()
