import yaml
from pathlib import Path


def build_evaluation_prompt():
    config_path = Path(__file__).parent / "prompts.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    template = data["evaluation_template"]
    dims = template["dimensions"]
    result = f"评估维度：\n"
    for d in dims:
        result += f"- {d['name']}: {d['description']}\n"
    return result


def build_regeneration_prompt():
    config_path = Path(__file__).parent / "prompts.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["regeneration_template"]


def get_template_types():
    return ["simple", "thermal", "spatial", "distant", "hidden"]
