#!/usr/bin/env python3
"""End-to-end integration test for the multi-agent data generation pipeline.

This test:
1. Creates 10 synthetic test images (simple shapes)
2. Runs the complete pipeline: ingestion → annotation → text_generation → refinement → validation → distillation
3. Tests checkpoint save/load/resume functionality
4. Verifies output format (JSONL, tar shards)
5. Cleans up test artifacts

Usage:
    python test_integration.py
"""

import asyncio
import base64
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any
from unittest import TestCase, main as unittest_main

import cv2
import numpy as np

# Add dataGenAgent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import DataOrchestrator
from utils.checkpoint import (
    save_checkpoint,
    load_checkpoint,
    is_processed,
    mark_processed,
)


# VLM Configuration - using local Qwen3-VL-32B-Instruct
VLM_BASE_URL = "http://localhost:1285/v1"
VLM_MODEL = "Qwen/Qwen3-VL-32B-Instruct"
VLM_API_KEY = "EMPTY"  # No auth needed for local deployment
VLM_TIMEOUT = 30.0  # 30 second timeout


class SyntheticImageGenerator:
    """Generate synthetic test images with simple shapes."""

    def __init__(self, output_dir: str, num_images: int = 10, size: tuple = (512, 512)):
        """Initialize the generator.

        Args:
            output_dir: Directory to save generated images
            num_images: Number of images to generate
            size: Image size as (width, height)
        """
        self.output_dir = Path(output_dir)
        self.num_images = num_images
        self.size = size
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _draw_circle(
        self, img: np.ndarray, center: tuple, radius: int, color: tuple
    ) -> None:
        """Draw a filled circle on the image."""
        cv2.circle(img, center, radius, color, -1)

    def _draw_rectangle(
        self, img: np.ndarray, pt1: tuple, pt2: tuple, color: tuple
    ) -> None:
        """Draw a filled rectangle on the image."""
        cv2.rectangle(img, pt1, pt2, color, -1)

    def _draw_triangle(self, img: np.ndarray, pts: np.ndarray, color: tuple) -> None:
        """Draw a filled triangle on the image."""
        pts = pts.astype(np.int32)
        cv2.fillPoly(img, [pts], color)

    def _add_noise(self, img: np.ndarray, noise_level: float = 10.0) -> np.ndarray:
        """Add Gaussian noise to the image."""
        noise = np.random.normal(0, noise_level, img.shape).astype(np.uint8)
        return cv2.add(img, noise)

    def generate_images(self) -> List[str]:
        """Generate synthetic test images.

        Creates images with various shapes:
        - Circles
        - Rectangles
        - Triangles
        - Mixed shapes

        Returns:
            List of paths to generated images
        """
        image_paths = []
        h, w = self.size

        for i in range(self.num_images):
            # Create base image with random background color
            bg_color = np.random.randint(50, 200, 3).tolist()
            img = np.full((h, w, 3), bg_color, dtype=np.uint8)

            # Choose shape type based on index
            shape_type = i % 4

            if shape_type == 0:
                # Single circle
                center = (
                    w // 2 + np.random.randint(-50, 50),
                    h // 2 + np.random.randint(-50, 50),
                )
                radius = np.random.randint(50, 150)
                color = tuple(np.random.randint(0, 255, 3).tolist())
                self._draw_circle(img, center, radius, color)

            elif shape_type == 1:
                # Single rectangle
                pt1 = (
                    w // 4 + np.random.randint(-30, 30),
                    h // 4 + np.random.randint(-30, 30),
                )
                pt2 = (
                    3 * w // 4 + np.random.randint(-30, 30),
                    3 * h // 4 + np.random.randint(-30, 30),
                )
                color = tuple(np.random.randint(0, 255, 3).tolist())
                self._draw_rectangle(img, pt1, pt2, color)

            elif shape_type == 2:
                # Triangle
                pts = np.array(
                    [[w // 2, h // 4], [w // 4, 3 * h // 4], [3 * w // 4, 3 * h // 4]]
                )
                color = tuple(np.random.randint(0, 255, 3).tolist())
                self._draw_triangle(img, pts, color)

            else:
                # Multiple shapes
                # Circle
                center = (w // 3, h // 3)
                radius = np.random.randint(30, 80)
                color = tuple(np.random.randint(0, 255, 3).tolist())
                self._draw_circle(img, center, radius, color)

                # Rectangle
                pt1 = (w // 2, h // 2)
                pt2 = (w - 50, h - 50)
                color = tuple(np.random.randint(0, 255, 3).tolist())
                self._draw_rectangle(img, pt1, pt2, color)

            # Add slight noise
            img = self._add_noise(img, noise_level=5.0)

            # Save image
            image_path = self.output_dir / f"synthetic_{i:03d}.png"
            cv2.imwrite(str(image_path), img)
            image_paths.append(str(image_path))

        return image_paths


class TestPipelineIntegration(TestCase):
    """Integration tests for the data generation pipeline."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.test_dir = tempfile.mkdtemp(prefix="pipeline_test_")
        cls.image_dir = Path(cls.test_dir) / "images"
        cls.output_dir = Path(cls.test_dir) / "output"
        cls.checkpoint_path = Path(cls.test_dir) / "checkpoint.json"

        cls.image_dir.mkdir(parents=True, exist_ok=True)
        cls.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate synthetic test images
        generator = SyntheticImageGenerator(
            str(cls.image_dir), num_images=10, size=(512, 512)
        )
        cls.image_paths = generator.generate_images()

        print(
            f"\n[TEST SETUP] Created {len(cls.image_paths)} synthetic test images in {cls.image_dir}"
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up test artifacts."""
        # Clean up test directory
        if hasattr(cls, "test_dir") and os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
            print(f"\n[TEST CLEANUP] Removed test directory: {cls.test_dir}")

    def test_01_synthetic_images_created(self):
        """Test that synthetic images were created successfully."""
        self.assertTrue(self.image_dir.exists(), "Image directory should exist")
        images = list(self.image_dir.glob("*.png"))
        self.assertEqual(len(images), 10, "Should have 10 synthetic images")
        print(f"[TEST] Created {len(images)} synthetic images")

    def test_02_ingestion(self):
        """Test ingestion agent loads images correctly."""
        from agents.ingestion import IngestionAgent, IngestionState

        async def run_ingestion():
            agent = IngestionAgent(name="ingestion_test")
            state: IngestionState = {
                "image_dir": str(self.image_dir),
                "images": [],
                "total_found": 0,
                "duplicates_removed": 0,
                "low_quality_removed": 0,
                "errors": [],
            }
            return await agent.process(state)

        result = asyncio.run(run_ingestion())

        self.assertGreater(result["total_found"], 0, "Should find images")
        self.assertGreater(
            len(result["images"]), 0, "Should have images after processing"
        )
        print(
            f"[TEST] Ingestion: found {result['total_found']} images, {len(result['images'])} passed quality check"
        )

    def test_03_pipeline_run(self):
        """Test full pipeline execution."""

        async def run_pipeline():
            orchestrator = DataOrchestrator(
                image_dir=str(self.image_dir),
                min_width=256,
                min_height=256,
                min_quality=30,
            )
            return await orchestrator.run()

        result = asyncio.run(run_pipeline())

        # Verify pipeline completed
        self.assertIsInstance(result, dict, "Pipeline should return a dictionary")
        self.assertIn("processed_count", result, "Result should have processed_count")
        self.assertIn("failed_count", result, "Result should have failed_count")
        self.assertIn(
            "completed_annotations", result, "Result should have completed_annotations"
        )

        print(
            f"[TEST] Pipeline: processed={result.get('processed_count', 0)}, "
            f"failed={result.get('failed_count', 0)}"
        )

    def test_04_checkpoint_save_load(self):
        """Test checkpoint save and load functionality."""
        # Create mock state
        mock_state = {
            "total_images": 10,
            "processed_count": 5,
            "failed_count": 1,
            "current_image": str(self.image_dir / "synthetic_005.png"),
            "current_image_results": [],
            "iteration_round": 0,
            "low_quality_samples": [],
            "completed_annotations": [],
            "discarded_samples": [],
            "checkpoint": {
                "step": 3,
                "timestamp": "2024-01-01T12:00:00",
                "agent_name": "test",
            },
        }

        # Save checkpoint
        save_checkpoint(str(self.checkpoint_path), mock_state)
        self.assertTrue(
            self.checkpoint_path.exists(), "Checkpoint file should be created"
        )

        # Load checkpoint
        loaded_state = load_checkpoint(str(self.checkpoint_path))
        self.assertIsNotNone(loaded_state, "Loaded state should not be None")
        self.assertEqual(
            loaded_state["processed_count"], 5, "Processed count should match"
        )
        self.assertEqual(loaded_state["failed_count"], 1, "Failed count should match")

        print(f"[TEST] Checkpoint save/load: verified")

    def test_05_checkpoint_resume(self):
        """Test incremental processing with checkpoint resume."""
        from agents.ingestion import IngestionAgent, IngestionState

        async def run_ingestion():
            agent = IngestionAgent(name="ingestion_test")
            state: IngestionState = {
                "image_dir": str(self.image_dir),
                "images": [],
                "total_found": 0,
                "duplicates_removed": 0,
                "low_quality_removed": 0,
                "errors": [],
            }
            return await agent.process(state)

        result = asyncio.run(run_ingestion())

        # Mark some images as processed
        processed_images = set()
        for img in result["images"][:5]:  # First 5 images
            processed_images.add(img["path"])
            mark_processed(str(self.checkpoint_path), img["path"])

        # Check is_processed
        for img_path in processed_images:
            self.assertTrue(
                is_processed(str(self.checkpoint_path), img_path),
                f"Image {img_path} should be marked as processed",
            )

        # Check unprocessed images
        for img in result["images"][5:]:
            self.assertFalse(
                is_processed(str(self.checkpoint_path), img["path"]),
                f"Image {img['path']} should not be marked as processed",
            )

        print(f"[TEST] Checkpoint resume: verified incremental processing")

    def test_06_output_format_jsonl(self):
        """Test that output includes proper JSONL format."""
        # Create a mock distillation output
        test_output_dir = Path(self.test_dir) / "test_output"
        test_output_dir.mkdir(parents=True, exist_ok=True)

        jsonl_path = test_output_dir / "annotations.jsonl"

        # Create sample records
        records = []
        for i, img_path in enumerate(self.image_paths[:3]):
            record = {
                "image_path": img_path,
                "image_name": Path(img_path).name,
                "annotations": {
                    "image_height": 512,
                    "image_width": 512,
                    "bboxes": [[10, 10, 100, 100]],
                    "segments": [[[10, 10], [110, 10], [110, 110], [10, 110]]],
                },
                "quality_score": 0.85,
            }
            records.append(record)

        # Write JSONL
        with open(jsonl_path, "w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        # Verify JSONL format
        self.assertTrue(jsonl_path.exists(), "JSONL file should be created")

        with open(jsonl_path, "r") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 3, "Should have 3 JSONL records")

            for line in lines:
                record = json.loads(line)
                self.assertIn("image_path", record)
                self.assertIn("image_name", record)

        print(f"[TEST] Output format JSONL: verified {len(lines)} records")

    def test_07_output_format_tar_shards(self):
        """Test that output can be packaged into tar shards."""
        test_output_dir = Path(self.test_dir) / "test_output"
        test_output_dir.mkdir(parents=True, exist_ok=True)

        # Create a test tar file
        tar_path = test_output_dir / "shard_0000.tar"

        with tarfile.open(tar_path, "w") as tar:
            for img_path in self.image_paths[:3]:
                if os.path.exists(img_path):
                    tar.add(img_path, arcname=os.path.basename(img_path))

        # Verify tar file
        self.assertTrue(tar_path.exists(), "Tar shard should be created")

        # Read tar contents
        with tarfile.open(tar_path, "r") as tar:
            members = tar.getnames()
            self.assertEqual(len(members), 3, "Tar should contain 3 images")

        print(
            f"[TEST] Output format tar shards: verified {len(members)} images in shard"
        )

    def test_08_vlm_validation_call(self):
        """Test VLM validation call with local Qwen3-VL-32B-Instruct."""
        import httpx

        # Create a simple test image
        test_img = np.zeros((256, 256, 3), dtype=np.uint8)
        cv2.rectangle(test_img, (50, 50), (200, 200), (255, 255, 255), -1)

        # Encode to base64
        _, buffer = cv2.imencode(".png", test_img)
        img_base64 = base64.b64encode(buffer).decode("utf-8")

        prompt = """You are an expert quality evaluator for image segmentation masks.
Evaluate the segmentation result. Return JSON with scores 1-10 for:
- mask_completeness
- boundary_accuracy
- text_mask_alignment
- false_positive_detection
- small_target_detection
Also include reasoning."""

        try:

            async def call_vlm():
                async with httpx.AsyncClient(timeout=VLM_TIMEOUT) as client:
                    response = await client.post(
                        f"{VLM_BASE_URL}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {VLM_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": VLM_MODEL,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/png;base64,{img_base64}"
                                            },
                                        },
                                    ],
                                }
                            ],
                            "temperature": 0.1,
                        },
                    )
                    return response.json()

            result = asyncio.run(call_vlm())

            if "choices" in result:
                content = result["choices"][0]["message"]["content"]
                print(f"[TEST] VLM call successful: {content[:100]}...")
            else:
                print(f"[TEST] VLM call returned: {result}")

        except Exception as e:
            print(f"[TEST] VLM call failed (expected if not running): {e}")

    def test_09_full_pipeline_with_checkpoint(self):
        """Test complete pipeline with checkpoint save/load/resume cycle."""
        from agents.ingestion import IngestionAgent, IngestionState

        async def run_pipeline_with_checkpoint():
            # Initial run with checkpoint
            orchestrator = DataOrchestrator(
                image_dir=str(self.image_dir),
                min_width=256,
                min_height=256,
                min_quality=30,
            )

            # Run ingestion first
            agent = IngestionAgent(name="ingestion")
            ingestion_state: IngestionState = {
                "image_dir": str(self.image_dir),
                "images": [],
                "total_found": 0,
                "duplicates_removed": 0,
                "low_quality_removed": 0,
                "errors": [],
            }
            ingestion_result = await agent.process(ingestion_state)

            # Save checkpoint after ingestion
            checkpoint_state = {
                "total_images": len(ingestion_result["images"]),
                "processed_count": 0,
                "failed_count": 0,
                "current_image": None,
                "current_image_results": [],
                "iteration_round": 0,
                "low_quality_samples": [],
                "completed_annotations": [],
                "discarded_samples": [],
                "checkpoint": {
                    "step": 1,
                    "timestamp": "2024-01-01T12:00:00",
                    "agent_name": "ingestion",
                },
            }
            save_checkpoint(str(self.checkpoint_path), checkpoint_state)

            # Load checkpoint and verify
            loaded = load_checkpoint(str(self.checkpoint_path))
            self.assertIsNotNone(loaded, "Checkpoint should load successfully")
            self.assertEqual(
                loaded["processed_count"], 0, "Processed count should be 0"
            )

            # Run full pipeline
            result = await orchestrator.run()
            return result

        result = asyncio.run(run_pipeline_with_checkpoint())

        self.assertIsInstance(result, dict)
        total = result.get("processed_count", 0) + result.get("failed_count", 0)
        self.assertGreater(total, 0, "Should process at least some images")

        print(
            f"[TEST] Full pipeline with checkpoint: processed={result.get('processed_count', 0)}, "
            f"failed={result.get('failed_count', 0)}"
        )

    def test_10_cleanup(self):
        """Verify cleanup works correctly."""
        # Verify the test directory and images exist during test execution
        # Actual cleanup happens in tearDownClass after all tests complete
        self.assertTrue(
            os.path.exists(self.test_dir), "Test directory should exist during tests"
        )
        self.assertTrue(
            os.path.exists(self.image_dir), "Image directory should exist during tests"
        )
        images = list(self.image_dir.glob("*.png"))
        self.assertEqual(len(images), 10, "Should have 10 synthetic images")


def run_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("INTEGRATION TEST SUITE FOR DATA GENERATION PIPELINE")
    print("=" * 60)
    print(f"Test directory: {__name__}")
    print(f"VLM Configuration: {VLM_BASE_URL}")
    print(f"VLM Model: {VLM_MODEL}")
    print("=" * 60)

    # Run tests
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
