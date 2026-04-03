"""Unit tests for distillation agent."""

import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.distillation import DistillationAgent, DistillationState


class TestDistillationAgent(TestCase):
    """Tests for DistillationAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.agent = DistillationAgent(name="test_distillation")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_distillation_agent_initialization(self):
        """Test DistillationAgent initialization."""
        self.assertEqual(self.agent.name, "test_distillation")
        self.assertEqual(self.agent._images_per_shard, 1000)

    def test_get_shard_info(self):
        """Test getting shard information."""
        info = self.agent.get_shard_info(5000)
        self.assertEqual(info["num_images"], 5000)
        self.assertEqual(info["images_per_shard"], 1000)
        self.assertEqual(info["num_shards"], 5)

    def test_get_shard_info_with_remainder(self):
        """Test getting shard info with remainder."""
        info = self.agent.get_shard_info(5500)
        self.assertEqual(info["num_images"], 5500)
        self.assertEqual(info["num_shards"], 6)
        self.assertEqual(info["remainder"], 500)


class TestDistillationState(TestCase):
    """Tests for DistillationState."""

    def test_distillation_state_creation(self):
        """Test creating DistillationState."""
        state: DistillationState = {
            "image_paths": [],
            "teacher_features": None,
            "output_dir": "/output",
            "tar_shards": [],
            "jsonl_output": "/output/annotations.jsonl",
            "metadata": {},
        }

        self.assertEqual(state["output_dir"], "/output")
        self.assertEqual(state["tar_shards"], [])


if __name__ == "__main__":
    import unittest

    unittest.main()
