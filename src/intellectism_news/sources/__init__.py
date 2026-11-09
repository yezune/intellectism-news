"""Field source collectors. Each module returns (items, errors)."""

from __future__ import annotations

from datetime import date
from typing import Any

from ..models import Item
from . import api, arxiv, rss


def fetch_all(field: dict[str, Any], run_date: date) -> tuple[list[Item], dict[str, str]]:
    items: list[Item] = []
    errors: dict[str, str] = {}
    sources = field.get("sources", {})
    if "rss" in sources and sources["rss"].get("enabled", True):
        got, err = rss.fetch(sources["rss"], run_date, field["id"])
        items.extend(got)
        errors.update(err)
    if "api" in sources and sources["api"].get("enabled", True):
        got, err = api.fetch(sources["api"], run_date, field["id"])
        items.extend(got)
        errors.update(err)
    if "arxiv" in sources and sources["arxiv"].get("enabled", True):
        got, err = arxiv.fetch(sources["arxiv"], run_date, field["id"])
        items.extend(got)
        errors.update(err)
    return items, errors
