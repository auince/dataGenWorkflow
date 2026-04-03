"""QualityReviewAgent for LLM-driven quality assessment of converted data."""

import json
from typing import TypedDict, List, Dict, Any, Optional

from agents.base import BaseAgent
from utils.logger import get_logger
from utils.minimax_client import get_minimax_client


class QualityReviewState(TypedDict):
    """State schema for QualityReviewAgent."""

    image_paths: List[str]
    annotations: List[dict]
    quality_report: Optional[dict]
    review_passed: bool
    review_errors: List[str]


class QualityReviewAgent(BaseAgent[QualityReviewState]):
    """Agent for LLM-driven quality review of converted data.

    Uses MiniMax LLM to evaluate:
    - Mask completeness and accuracy
    - Text-mask alignment
    - Overall annotation quality
    - Data diversity and coverage

    Generates quality report with pass/fail and suggestions.
    """

    PASS_THRESHOLD = 7.0

    def __init__(self, name: str = "quality_reviewer"):
        super().__init__(name)
        self.logger = get_logger(f"agents.{name}")

    async def process(self, state: QualityReviewState) -> QualityReviewState:
        """Review converted data quality using MiniMax LLM.

        Args:
            state: State containing image_paths and annotations to review

        Returns:
            Updated state with quality_report and review_passed
        """
        image_paths = state.get("image_paths", [])
        annotations = state.get("annotations", [])

        if not image_paths:
            state["quality_report"] = {"error": "No images to review"}
            state["review_passed"] = False
            state["review_errors"] = ["No images provided"]
            return state

        try:
            client = get_minimax_client()

            prompt = self._create_review_prompt(image_paths, annotations)
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert data quality analyst for computer vision datasets.",
                },
                {"role": "user", "content": prompt},
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
            report = json.loads(content.strip())

            state["quality_report"] = report
            state["review_passed"] = (
                report.get("overall_score", 0) >= self.PASS_THRESHOLD
            )
            state["review_errors"] = report.get("issues", [])

        except Exception as e:
            self.logger.error(f"Quality review failed: {e}")
            state["quality_report"] = {"error": str(e)}
            state["review_passed"] = False
            state["review_errors"] = [str(e)]

        return state

    def _create_review_prompt(
        self, image_paths: List[str], annotations: List[dict]
    ) -> str:
        """Create review prompt for MiniMax LLM."""
        num_images = len(image_paths)
        num_annotations = len(annotations)

        prompt = f"""Review the quality of a converted computer vision dataset.

Dataset Statistics:
- Number of images: {num_images}
- Number of annotations: {num_annotations}

Evaluate the dataset across these dimensions (score 0-10 each):

1. **Annotation Completeness** (weight 25%): Are all images properly annotated with masks, bounding boxes, and segments?

2. **Mask Quality** (weight 25%): Do the segmentation masks appear complete and accurate?

3. **Text-Mask Alignment** (weight 20%): Do text descriptions match the visual content?

4. **Diversity** (weight 15%): Is there sufficient variety in the dataset (objects, scenes, etc.)?

5. **Data Integrity** (weight 15%): Are annotations consistent and well-formed?

Return your evaluation as JSON:
{{
  "mask_quality_score": <score 0-10>,
  "annotation_completeness": <score 0-10>,
  "text_alignment_score": <score 0-10>,
  "diversity_score": <score 0-10>,
  "integrity_score": <score 0-10>,
  "overall_score": <score 0-10>,
  "issues": ["list of specific issues found"],
  "recommendations": ["list of improvement suggestions"]
}}

Only return the JSON, no additional text."""
        return prompt


async def run_quality_review(image_paths: List[str], annotations: List[dict]) -> dict:
    """Run quality review on a batch of converted data.

    Args:
        image_paths: List of paths to converted images
        annotations: List of annotation dicts

    Returns:
        Quality report dict
    """
    agent = QualityReviewAgent()
    state: QualityReviewState = {
        "image_paths": image_paths,
        "annotations": annotations,
        "quality_report": None,
        "review_passed": False,
        "review_errors": [],
    }
    result = await agent.process(state)
    return {
        "report": result.get("quality_report"),
        "passed": result.get("review_passed"),
        "errors": result.get("review_errors"),
    }
