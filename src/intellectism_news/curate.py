"""Curation: relevance, duplicate merging, scoring, and selection."""

from __future__ import annotations

from typing import Any

from .models import Item

RELEVANCE_CAP = 6.0


def relevance(item: Item, keywords: dict[str, float]) -> float:
    text = f"{item.title} {item.summary} {' '.join(item.tags)}".lower()
    return sum(weight for keyword, weight in keywords.items() if keyword in text)


def requires_keywords(item: Item, config: dict[str, Any]) -> bool:
    sources = config.get("sources", {})
    if item.source.startswith("rss:"):
        name = item.source.split(":", 1)[1]
        feed = next(
            (feed for feed in sources.get("rss", {}).get("feeds", []) if feed["name"] == name),
            {},
        )
        return bool(feed.get("require_keywords", False))
    if item.source.startswith("api:"):
        name = item.source.split(":", 1)[1]
        source = next(
            (
                source
                for source in sources.get("api", {}).get("sources", [])
                if source["name"] == name
            ),
            {},
        )
        return bool(source.get("require_keywords", False))
    return bool(sources.get(item.source, {}).get("require_keywords", False))


def source_weight(item: Item, config: dict[str, Any]) -> float:
    if item.source.startswith("rss:"):
        key = "rss"
    elif item.source.startswith("api:"):
        key = "api"
    else:
        key = item.source
    return float(config.get("sources", {}).get(key, {}).get("weight", 1.0))


def merge_duplicates(items: list[Item]) -> list[Item]:
    by_id: dict[str, Item] = {}
    for item in items:
        current = by_id.get(item.id)
        if current is None:
            by_id[item.id] = item
            continue
        if len(item.summary) > len(current.summary):
            current.summary = item.summary
        current.tags = list(dict.fromkeys(current.tags + item.tags))
        if current.primary_source is None:
            current.primary_source = item.primary_source
    return list(by_id.values())


def score(item: Item, config: dict[str, Any]) -> float:
    rel = relevance(item, config.get("keywords", {}))
    return round(source_weight(item, config) * (1 + min(rel, RELEVANCE_CAP) / 2), 3)


def curate(
    items: list[Item], config: dict[str, Any], seen: dict[str, str], run_date: str
) -> list[Item]:
    keywords = config.get("keywords", {})
    min_relevance = float(config.get("min_relevance", 0))
    pool: list[Item] = []
    for item in merge_duplicates(items):
        first = seen.get(item.id)
        if first is not None and first != run_date:
            continue
        if requires_keywords(item, config) and relevance(item, keywords) < min_relevance:
            continue
        item.score = score(item, config)
        pool.append(item)

    limits = config.get("limits", {})
    candidates = int(limits.get("candidates", 10))
    max_items = int(limits.get("max_items", 20))
    max_per_source = int(limits.get("max_per_source", 3))

    ranked = sorted(pool, key=lambda item: (-item.score, item.id))[:max_items]
    counts: dict[str, int] = {}
    selected: list[Item] = []
    for item in ranked:
        if len(selected) >= candidates:
            break
        if counts.get(item.source, 0) >= max_per_source:
            continue
        counts[item.source] = counts.get(item.source, 0) + 1
        item.candidate = True
        selected.append(item)
    return selected
