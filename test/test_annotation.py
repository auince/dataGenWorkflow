"""Unit tests for annotation agent."""

import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
import shutil

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.annotation import AnnotationAgent, AnnotationState


class TestAnnotationAgent(TestCase):
    """Tests for AnnotationAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.model_path = "/data/lch/SAM/ultralytics-main/sam3.pt"

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_annotation_agent_initialization(self):
        """Test AnnotationAgent initialization."""
        agent = AnnotationAgent(name="test_annotation")
        self.assertEqual(agent.name, "test_annotation")
        self.assertEqual(agent.model_path, "/data/lch/SAM/ultralytics-main/sam3.pt")

    def test_resize_image(self):
        """Test image resizing."""
        agent = AnnotationAgent(name="test_annotation")
        img = np.zeros((100, 100, 3), dtype=np.uint8)

        resized = agent._resize_image(img, 2.0)
        self.assertEqual(resized.shape, (200, 200, 3))

    def test_resize_image_same_scale(self):
        """Test image resizing with scale 1.0."""
        agent = AnnotationAgent(name="test_annotation")
        img = np.zeros((100, 100, 3), dtype=np.uint8)

        resized = agent._resize_image(img, 1.0)
        self.assertEqual(resized.shape, (100, 100, 3))

    def test_detect_small_targets(self):
        """Test small target detection."""
        agent = AnnotationAgent(name="test_annotation")

        # Create a small mask (8x8 pixels)
        small_mask = np.zeros((10, 10), dtype=np.uint8)
        small_mask[1:9, 1:9] = 1

        # Create a large mask
        large_mask = np.zeros((100, 100), dtype=np.uint8)
        large_mask[10:90, 10:90] = 1

        small_targets = agent._detect_small_targets(
            [small_mask, large_mask], (100, 100)
        )
        self.assertEqual(len(small_targets), 1)


class TestAnnotationState(TestCase):
    """Tests for AnnotationState."""

    def test_annotation_state_creation(self):
        """Test creating AnnotationState."""
        state: AnnotationState = {
            "current_image": "/path/to/image.png",
            "annotations": {},
            "masks": [],
            "small_target_masks": [],
        }

        self.assertEqual(state["current_image"], "/path/to/image.png")
        self.assertEqual(state["masks"], [])


if __name__ == "__main__":
    import unittest

    unittest.main()
