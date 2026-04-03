"""Unit tests for validation agent."""

import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
import shutil

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.validation import ValidationAgent, ValidationState


class TestValidationAgent(TestCase):
    """Tests for ValidationAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.agent = ValidationAgent(name="test_validation")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_validation_agent_initialization(self):
        """Test ValidationAgent initialization."""
        self.assertEqual(self.agent.name, "test_validation")
        self.assertEqual(self.agent.model, "kimi-vl-alpha")
        self.assertEqual(self.agent.PASS_THRESHOLD, 7.0)
        self.assertEqual(self.agent.REGENERATE_THRESHOLD, 5.0)

    def test_encode_image_to_base64(self):
        """Test image encoding to base64."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = self.agent._encode_image_to_base64(img)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_calculate_weighted_score(self):
        """Test weighted score calculation."""
        scores = {
            "mask_completeness": 8.0,
            "boundary_accuracy": 7.0,
            "text_mask_alignment": 6.0,
            "false_positive_detection": 7.0,
            "small_target_detection": 8.0,
        }

        result = self.agent._calculate_weighted_score(scores)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_get_evaluation_result_pass(self):
        """Test evaluation result for passing score."""
        self.assertEqual(self.agent._get_evaluation_result(8.0), "pass")
        self.assertEqual(self.agent._get_evaluation_result(7.0), "pass")

    def test_get_evaluation_result_regenerate(self):
        """Test evaluation result for regenerate score."""
        self.assertEqual(self.agent._get_evaluation_result(6.0), "regenerate")
        self.assertEqual(self.agent._get_evaluation_result(5.0), "regenerate")

    def test_get_evaluation_result_discard(self):
        """Test evaluation result for discard score."""
        self.assertEqual(self.agent._get_evaluation_result(4.0), "discard")
        self.assertEqual(self.agent._get_evaluation_result(0.0), "discard")

    def test_heuristic_evaluation(self):
        """Test heuristic evaluation fallback."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        masks = [np.ones((10, 10), dtype=np.uint8)]
        annotations = {"expected_objects": 1}

        result = self.agent._heuristic_evaluation(img, masks, annotations)
        self.assertIn("mask_completeness", result)
        self.assertIn("boundary_accuracy", result)
        self.assertIn("text_mask_alignment", result)
        self.assertIn("false_positive_detection", result)
        self.assertIn("small_target_detection", result)


class TestValidationState(TestCase):
    """Tests for ValidationState."""

    def test_validation_state_creation(self):
        """Test creating ValidationState."""
        state: ValidationState = {
            "current_image": "/path/to/image.png",
            "masks": [],
            "annotations": {},
            "quality_score": 8.5,
            "evaluation_result": "pass",
            "evaluation_details": {},
        }

        self.assertEqual(state["evaluation_result"], "pass")
        self.assertEqual(state["quality_score"], 8.5)


if __name__ == "__main__":
    import unittest

    unittest.main()
