from langgraph.graph import StateGraph, START, END
from typing import TypedDict

from graph.state import PipelineState
from graph.nodes import (
    node_ingestion,
    node_next_image,
    node_prompt_generation,
    node_annotation,
    node_refinement,
    node_distillation,
)


class PipelineStateInput(TypedDict):
    image_dir: str
    output_dir: str
    images: list
    vlm_cache_dir: str
    completed_annotations: list


class PipelineStateOutput(TypedDict):
    total_images: int
    processed_count: int
    failed_count: int
    completed_annotations: list
    discarded_samples: list
    distilled_samples: list
    distillation_metrics: dict
    generated_prompts: list


def create_workflow() -> StateGraph:
    builder = StateGraph(PipelineState, output_schema=PipelineStateOutput)

    builder.add_node("ingestion", node_ingestion)
    builder.add_node("next_image", node_next_image)
    builder.add_node("prompt_generation", node_prompt_generation)
    builder.add_node("annotation", node_annotation)
    builder.add_node("refinement", node_refinement)
    builder.add_node("distillation", node_distillation)

    builder.add_edge(START, "ingestion")
    builder.add_edge("ingestion", "next_image")
    builder.add_edge("next_image", "prompt_generation")

    def route_from_prompt_generation(state: PipelineState) -> str:
        if state.get("current_image") is None:
            return "distillation"
        return "annotation"

    builder.add_conditional_edges(
        "prompt_generation",
        route_from_prompt_generation,
        {
            "annotation": "annotation",
            "distillation": "distillation",
        },
    )

    builder.add_edge("annotation", "refinement")
    builder.add_edge("refinement", "distillation")

    def route_from_next_image(state: PipelineState) -> str:
        if state.get("current_image") is None:
            return "__end__"
        return "prompt_generation"

    builder.add_conditional_edges(
        "next_image",
        route_from_next_image,
        {
            "prompt_generation": "prompt_generation",
            "__end__": END,
        },
    )

    def route_from_distillation(state: PipelineState) -> str:
        if state.get("current_image") is None:
            return "__end__"
        return "next_image"

    builder.add_conditional_edges(
        "distillation",
        route_from_distillation,
        {
            "next_image": "next_image",
            "__end__": END,
        },
    )

    return builder.compile()
