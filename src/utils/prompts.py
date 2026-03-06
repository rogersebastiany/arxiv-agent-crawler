"""Load prompt templates from YAML files in the prompts/ directory."""

from __future__ import annotations

from pathlib import Path

import yaml

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def load_prompt(name: str) -> dict[str, str]:
    """Load a prompt YAML file by name (without extension).

    Returns a dict mapping prompt keys to template strings.
    """
    path = PROMPTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)
