"""Text generation agent using MiniMax LLM for intelligent prompt generation."""

import random
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

from agents.base import BaseAgent
from graph.state import PipelineState
from utils.logger import get_logger
from utils.minimax_client import get_minimax_client


class TextGenAgent(BaseAgent[PipelineState]):
    """Agent that generates text prompts using MiniMax LLM.

    Uses MiniMax to generate contextually appropriate prompts based on
    image analysis when available, with vocabulary-based fallback.
    """

    def __init__(self, name: str = "text_generator"):
        super().__init__(name)
        self.vocabulary: Dict[str, Any] = {}
        self._load_vocabulary()
        self.logger = get_logger(f"agents.{name}")

    def _load_vocabulary(self) -> None:
        """Load vocabulary from config/vocabulary.yaml."""
        vocab_path = Path(__file__).parent.parent / "config" / "vocabulary.yaml"
        if vocab_path.exists():
            with open(vocab_path, "r") as f:
                self.vocabulary = yaml.safe_load(f) or {}
        else:
            self.vocabulary = self._default_vocabulary()

    def _default_vocabulary(self) -> Dict[str, Any]:
        """Return default vocabulary if file not found."""
        return {
            "categories": {
                "objects": ["object"],
                "actions": ["action"],
                "attributes": ["attribute"],
                "scenes": ["scene"],
            },
            "templates": {
                "simple": ["A {attribute} {object}"],
                "descriptive": ["A {attribute} {object} that is {action}"],
                "detailed": ["A {attribute} {object} {action} in a {scene}"],
            },
            "rules": {
                "min_prompts_per_image": 3,
                "max_prompts_per_image": 5,
            },
        }

    def get_random_item(self, category: str, subcategory: str) -> str:
        """Get a random item from a vocabulary subcategory."""
        items = self.vocabulary.get("categories", {}).get(subcategory, [])
        return random.choice(items) if items else subcategory

    def get_templates(self, length: str = "medium") -> List[str]:
        """Get templates based on desired prompt length."""
        templates = self.vocabulary.get("templates", {})
        if length == "short":
            return templates.get("simple", [])
        elif length == "long":
            return templates.get("detailed", [])
        return templates.get("descriptive", []) + templates.get("simple", [])

    def generate_prompt(self, template: str) -> str:
        """Generate a single prompt by filling in the template."""
        categories = self.vocabulary.get("categories", {})
        prompt = template

        placeholders = {
            "object": categories.get("objects", ["object"]),
            "action": categories.get("actions", ["action"]),
            "attribute": categories.get("attributes", ["attribute"]),
            "scene": categories.get("scenes", ["scene"]),
        }

        for placeholder, values in placeholders.items():
            placeholder_pattern = "{" + placeholder + "}"
            if placeholder_pattern in prompt and values:
                replacement = random.choice(values)
                prompt = prompt.replace(placeholder_pattern, replacement, 1)

        return prompt

    def generate_prompts(self, count: Optional[int] = None) -> List[str]:
        """Generate multiple unique prompts for an image."""
        rules = self.vocabulary.get("rules", {})
        min_prompts = rules.get("min_prompts_per_image", 3)
        max_prompts = rules.get("max_prompts_per_image", 5)

        if count is None:
            count = random.randint(min_prompts, max_prompts)

        length_pref = rules.get("prompt_length", "medium")
        templates = self.get_templates(length_pref)

        prompts = []
        for _ in range(count):
            if templates:
                template = random.choice(templates)
                prompt = self.generate_prompt(template)
                if prompt not in prompts:
                    prompts.append(prompt)

        return prompts

    async def process(self, state: PipelineState) -> PipelineState:
        """Process state and generate text prompts using MiniMax LLM."""
        current_image = state.get("current_image")
        if not current_image:
            return state

        prompts = await self._generate_with_minimax(current_image, state)

        if "generated_prompts" not in state:
            state["generated_prompts"] = []

        state["generated_prompts"].extend(prompts)

        return state

    async def _generate_with_minimax(
        self, image_path: str, state: PipelineState
    ) -> List[str]:
        """Generate prompts using MiniMax LLM with vocabulary fallback."""
        try:
            client = get_minimax_client()
            prompt_request = self._create_prompt_request(image_path, state)

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at generating descriptive prompts for image segmentation datasets.",
                },
                {"role": "user", "content": prompt_request},
            ]

            response = client.chat.completions.create(
                model="MiniMax-M2.7",
                messages=messages,
            )
            raw_content = response.choices[0].message.content

            if "</think>" in raw_content:
                content = raw_content.split("</think>")[1].split("<think>")[0].strip()
            else:
                content = raw_content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            prompts = result.get("prompts", [])

            if prompts:
                self.logger.info(f"MiniMax generated {len(prompts)} prompts")
                return prompts

        except Exception as e:
            self.logger.warning(
                f"MiniMax prompt generation failed: {e}, using vocabulary fallback"
            )

        return self.generate_prompts()

    def _create_prompt_request(self, image_path: str, state: PipelineState) -> str:
        """Create prompt request for MiniMax LLM."""
        masks = state.get("masks", [])
        annotations = state.get("annotations", {})
        num_masks = len(masks)
        description = annotations.get("description", "")

        return f"""Generate {self.vocabulary.get("rules", {}).get("min_prompts_per_image", 3)} to {self.vocabulary.get("rules", {}).get("max_prompts_per_image", 5)} descriptive prompts for image segmentation.

Image: {image_path}
Number of detected objects/masks: {num_masks}
Description: {description}

Generate prompts that:
1. Describe the main objects in the scene
2. Include attributes like size, color, position
3. Describe actions or interactions if applicable
4. Vary in length and specificity

Return as JSON:
{{
  "prompts": ["prompt 1", "prompt 2", ...]
}}

Only return the JSON, no additional text."""
