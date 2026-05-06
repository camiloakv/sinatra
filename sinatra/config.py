from pathlib import Path
from yaml import safe_load


CONFIG_PATH = Path(__file__).parent.parent / "sinatra.yaml"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return safe_load(f) or {}
    return {"max_file_size_mb": 1024, "max_duration_hours": 2}