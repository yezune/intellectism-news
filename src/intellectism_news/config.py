"""Field configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED_FIELD_KEYS = ("name", "question", "keywords", "sources", "limits")


def load_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_config(config: dict[str, Any]) -> None:
    if not isinstance(config, dict):
        raise ValueError("config must be a mapping")
    fields = config.get("fields")
    if not isinstance(fields, dict) or not fields:
        raise ValueError("config.fields must be a non-empty mapping")
    for field_id, field in fields.items():
        if not isinstance(field, dict):
            raise ValueError(f"fields.{field_id} must be a mapping")
        for key in REQUIRED_FIELD_KEYS:
            if key not in field:
                raise ValueError(f"fields.{field_id} missing {key}")
        if not isinstance(field["keywords"], dict):
            raise ValueError(f"fields.{field_id}.keywords must be a mapping")
        if not isinstance(field["sources"], dict):
            raise ValueError(f"fields.{field_id}.sources must be a mapping")
        if not isinstance(field["limits"], dict):
            raise ValueError(f"fields.{field_id}.limits must be a mapping")


def get_field(config: dict[str, Any], field_id: str) -> dict[str, Any]:
    fields = config.get("fields", {})
    if field_id not in fields:
        raise KeyError(f"unknown field: {field_id}")
    return {**fields[field_id], "id": field_id}


def list_fields(config: dict[str, Any]) -> list[str]:
    return sorted(config.get("fields", {}))
