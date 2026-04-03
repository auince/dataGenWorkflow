import yaml
from pathlib import Path


def load_vocabulary():
    config_path = Path(__file__).parent / "vocabulary.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
