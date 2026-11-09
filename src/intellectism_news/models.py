"""Data models for the field news pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Item:
    id: str
    field: str
    source: str
    title: str
    url: str
    published: str
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    score: float = 0.0
    primary_source: str | None = None
    candidate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunResult:
    date: str
    field: str
    generated_at: str
    fetched: int
    errors: dict[str, str]
    items: list[Item]
    candidates: list[str]
    retries: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "field": self.field,
            "generated_at": self.generated_at,
            "fetched": self.fetched,
            "errors": self.errors,
            "items": [item.to_dict() for item in self.items],
            "candidates": self.candidates,
            "retries": self.retries,
        }
