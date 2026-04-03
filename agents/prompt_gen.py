"""VLM-based concept label generator for SAM3 text-prompt segmentation."""

import base64
import json
import re
from typing import TypedDict, List, Optional

import cv2

from agents.base import BaseAgent
from utils.logger import get_logger
from utils.vlm_client import call_vlm


class PromptGenState(TypedDict):
    current_image: str
    text_prompts: List[str]
    vlm_raw_response: Optional[str]
    vlm_cache_dir: Optional[str]


class PromptGenAgent(BaseAgent[PromptGenState]):
    PROMPT_TEMPLATE = """Analyze this infrared/thermal image and identify the main concepts/objects that can be segmented.

Requirements:
- Generate 1-10 short concept labels (1-3 words each)
- Cover different scales: large objects AND small targets
- Use specific terms (e.g., "person" not "human", "car" not "vehicle")
- Focus on distinct, separable objects
- Only output concepts visible in the image

Return JSON format:
{{
  "concepts": ["concept1", "concept2", "concept3", ...]
}}

Only return valid JSON, no explanation."""

    def __init__(self, name: str = "prompt_generator"):
        super().__init__(name)
        self.logger = get_logger(f"agents.{name}")

    async def process(self, state: PromptGenState) -> PromptGenState:
        image_path = state.get("current_image")
        if not image_path:
            state["text_prompts"] = []
            state["vlm_raw_response"] = None
            return state

        vlm_cache_dir = state.get("vlm_cache_dir")
        if vlm_cache_dir:
            cached = self._load_from_cache(image_path, vlm_cache_dir)
            if cached:
                state["text_prompts"] = cached["concepts"]
                state["vlm_raw_response"] = cached["raw_response"]
                self.logger.info(f"Using cached VLM prompts for: {image_path}")
                return state

        self.logger.info(f"Generating prompts for: {image_path}")

        image = cv2.imread(image_path)
        if image is None:
            self.logger.warning(f"Failed to read image: {image_path}")
            state["text_prompts"] = []
            state["vlm_raw_response"] = None
            return state

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode(".png", image_rgb)
        img_base64 = base64.b64encode(buffer).decode("utf-8")

        try:
            response = call_vlm(img_base64, self.PROMPT_TEMPLATE)
            state["vlm_raw_response"] = response
            concepts = self._parse_response(response)
            state["text_prompts"] = concepts
            self.logger.info(f"Generated {len(concepts)} prompts: {concepts}")

            if vlm_cache_dir:
                self._save_to_cache(image_path, vlm_cache_dir, concepts, response)
        except Exception as e:
            self.logger.error(f"VLM call failed: {e}")
            state["text_prompts"] = ["object"]
            state["vlm_raw_response"] = None

        return state

    def _load_from_cache(self, image_path: str, cache_dir: str) -> dict | None:
        from pathlib import Path

        img_name = Path(image_path).stem
        cache_path = Path(cache_dir) / f"vlm_{img_name}.json"
        if cache_path.exists():
            try:
                with open(cache_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def _save_to_cache(
        self, image_path: str, cache_dir: str, concepts: list, raw_response: str
    ):
        from pathlib import Path

        img_name = Path(image_path).stem
        cache_path = Path(cache_dir) / f"vlm_{img_name}.json"
        try:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump({"concepts": concepts, "raw_response": raw_response}, f)
        except IOError as e:
            self.logger.warning(f"Failed to save VLM cache for {image_path}: {e}")

    def _parse_response(self, response: str) -> List[str]:
        content = response.strip()
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0]
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0]
        content = content.strip()

        try:
            data = json.loads(content)
            concepts = data.get("concepts", [])
            if isinstance(concepts, list) and concepts:
                concepts = [str(c).strip() for c in concepts if str(c).strip()]
                if concepts:
                    return concepts
        except json.JSONDecodeError:
            pass

        return self._extract_concepts_from_text(content)

    def _extract_concepts_from_text(self, text: str) -> List[str]:
        patterns = [r'"([^"]+)"', r"'([^']+)'", r"\[([^\]]+)\]"]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                concepts_str = matches[-1]
                concepts = [
                    c.strip().strip('"').strip("'") for c in concepts_str.split(",")
                ]
                concepts = [c for c in concepts if c]
                if concepts:
                    return concepts

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        concepts = []
        for line in lines:
            for prefix in ["concepts:", "- ", "* ", "• "]:
                if line.startswith(prefix):
                    line = line[len(prefix) :]
            line = line.strip().strip(",").strip()
            if line and len(line) < 30:
                concepts.append(line)

        return concepts[:10] if concepts else ["object"]
