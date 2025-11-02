"""File and path utility functions."""
import os
import json
from typing import Any, Dict


def ensure_dir(path: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)


def save_json(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """Save data to a JSON file."""
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_json(file_path: str) -> Dict[str, Any]:
    """Load data from a JSON file. Returns empty dict if file doesn't exist."""
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


