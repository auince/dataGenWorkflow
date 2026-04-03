"""Unit tests for ingestion agent."""

import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
import shutil

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.ingestion import (
    IngestionAgent,
    IngestionState,
    LoadImagesTool,
    DeduplicateImagesTool,
    QualityCheckTool,
)


class TestLoadImagesTool(TestCase):
    """Tests for LoadImagesTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.tool = LoadImagesTool()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_load_images_from_directory(self):
        """Test loading images from a directory."""
        # Create test images
        for i in range(3):
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(os.path.join(self.test_dir, f"image{i}.png"), img)

        result = self.tool.run(directory=self.test_dir)
        self.assertEqual(len(result), 3)

    def test_load_images_empty_directory(self):
        """Test loading images from an empty directory."""
        result = self.tool.run(directory=self.test_dir)
        self.assertEqual(len(result), 0)

    def test_load_images_nonexistent_directory(self):
        """Test loading images from a nonexistent directory."""
        with self.assertRaises(ValueError):
            self.tool.run(directory="/nonexistent/directory")


class TestQualityCheckTool(TestCase):
    """Tests for QualityCheckTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.tool = QualityCheckTool(min_width=100, min_height=100, min_quality=30)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_quality_check_pass(self):
        """Test quality check passing."""
        # Create a valid image
        img = np.random.randint(50, 200, (200, 200, 3), dtype=np.uint8)
        img_path = os.path.join(self.test_dir, "valid.png")
        cv2.imwrite(img_path, img)

        self.assertTrue(self.tool.run(image_path=img_path))

    def test_quality_check_too_small(self):
        """Test quality check failing for small image."""
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        img_path = os.path.join(self.test_dir, "small.png")
        cv2.imwrite(img_path, img)

        self.assertFalse(self.tool.run(image_path=img_path))

    def test_quality_check_too_dark(self):
        """Test quality check failing for dark image."""
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img_path = os.path.join(self.test_dir, "dark.png")
        cv2.imwrite(img_path, img)

        self.assertFalse(self.tool.run(image_path=img_path))

    def test_quality_check_low_contrast(self):
        """Test quality check failing for low contrast image."""
        img = np.full((200, 200, 3), 128, dtype=np.uint8)
        img_path = os.path.join(self.test_dir, "low_contrast.png")
        cv2.imwrite(img_path, img)

        self.assertFalse(self.tool.run(image_path=img_path))


class TestDeduplicateImagesTool(TestCase):
    """Tests for DeduplicateImagesTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.tool = DeduplicateImagesTool()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_deduplicate_images(self):
        """Test deduplicating images."""
        # Create two identical images
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        path1 = os.path.join(self.test_dir, "image1.png")
        path2 = os.path.join(self.test_dir, "image2.png")
        cv2.imwrite(path1, img)
        cv2.imwrite(path2, img)

        result = self.tool.run(image_paths=[path1, path2])
        self.assertEqual(len(result), 1)

    def test_deduplicate_different_images(self):
        """Test that different images are not deduplicated."""
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.ones((100, 100, 3), dtype=np.uint8) * 255

        path1 = os.path.join(self.test_dir, "image1.png")
        path2 = os.path.join(self.test_dir, "image2.png")
        cv2.imwrite(path1, img1)
        cv2.imwrite(path2, img2)

        result = self.tool.run(image_paths=[path1, path2])
        self.assertEqual(len(result), 2)


class TestIngestionAgent(TestCase):
    """Tests for IngestionAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.agent = IngestionAgent(name="test_ingestion")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_ingestion_agent_initialization(self):
        """Test IngestionAgent initialization."""
        self.assertEqual(self.agent.name, "test_ingestion")
        self.assertIsNotNone(self.agent.load_images_tool)
        self.assertIsNotNone(self.agent.deduplicate_tool)
        self.assertIsNotNone(self.agent.quality_check_tool)


if __name__ == "__main__":
    import unittest

    unittest.main()
