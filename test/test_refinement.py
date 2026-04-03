"""Unit tests for refinement agent."""

import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
import shutil

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.refinement import RefinementAgent, RefinementState


class TestRefinementAgent(TestCase):
    """Tests for RefinementAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.agent = RefinementAgent(name="test_refinement")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_refinement_agent_initialization(self):
        """Test RefinementAgent initialization."""
        self.assertEqual(self.agent.name, "test_refinement")
        self.assertEqual(self.agent._min_area, 4)
        self.assertEqual(self.agent._max_area_ratio, 0.90)

    def test_morphology_process(self):
        """Test morphology processing."""
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[25:75, 25:75] = 1

        result = self.agent._morphology_process(mask)
        self.assertEqual(result.shape, mask.shape)
        self.assertTrue(np.any(result > 0))

    def test_area_filter_pass(self):
        """Test area filter passing."""
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[25:75, 25:75] = 1
        total_area = 100 * 100

        self.assertTrue(self.agent._area_filter(mask, total_area))

    def test_area_filter_too_small(self):
        """Test area filter failing for small mask."""
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[50:51, 50:51] = 1
        total_area = 100 * 100

        self.assertFalse(self.agent._area_filter(mask, total_area))

    def test_area_filter_too_large(self):
        """Test area filter failing for large mask."""
        mask = np.ones((100, 100), dtype=np.uint8)
        total_area = 100 * 100

        self.assertFalse(self.agent._area_filter(mask, total_area))

    def test_boundary_refinement(self):
        """Test boundary refinement."""
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[25:75, 25:75] = 1

        result = self.agent._boundary_refinement(mask)
        self.assertEqual(result.shape, mask.shape)
        self.assertTrue(np.any(result > 0))


class TestRefinementState(TestCase):
    """Tests for RefinementState."""

    def test_refinement_state_creation(self):
        """Test creating RefinementState."""
        state: RefinementState = {
            "masks": [],
            "image_size": (512, 512),
            "refined_masks": [],
        }

        self.assertEqual(state["image_size"], (512, 512))
        self.assertEqual(state["refined_masks"], [])


if __name__ == "__main__":
    import unittest

    unittest.main()
