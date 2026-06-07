from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CategoryConfig:
    key: str
    label: str
    seed_queries: list[str]


@dataclass(frozen=True)
class AppConfig:
    categories: dict[str, CategoryConfig]
    scoring_weights: dict[str, int]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping at {path}")
    return data


def load_categories(path: Path | None = None) -> dict[str, CategoryConfig]:
    path = path or PROJECT_ROOT / "config" / "categories.yaml"
    data = _load_yaml(path)
    categories = data.get("categories", {})
    if not isinstance(categories, dict):
        raise ValueError("categories.yaml must contain a categories mapping")
    loaded: dict[str, CategoryConfig] = {}
    for key, value in categories.items():
        if not isinstance(value, dict):
            raise ValueError(f"Category {key} must be a mapping")
        queries = value.get("seed_queries", [])
        if not isinstance(queries, list) or not all(isinstance(item, str) for item in queries):
            raise ValueError(f"Category {key} seed_queries must be a list of strings")
        loaded[key] = CategoryConfig(
            key=key,
            label=str(value.get("label", key)),
            seed_queries=queries,
        )
    return loaded


def load_scoring_weights(path: Path | None = None) -> dict[str, int]:
    path = path or PROJECT_ROOT / "config" / "scoring.yaml"
    data = _load_yaml(path)
    weights = data.get("weights", {})
    if not isinstance(weights, dict):
        raise ValueError("scoring.yaml must contain a weights mapping")
    return {str(key): int(value) for key, value in weights.items()}


def load_app_config() -> AppConfig:
    return AppConfig(categories=load_categories(), scoring_weights=load_scoring_weights())
