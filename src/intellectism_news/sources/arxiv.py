"""arXiv API (Atom) collector."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import feedparser

from .. import http
from ..models import Item

API = "https://export.arxiv.org/api/query"


def fetch(
    cfg: dict[str, Any], run_date: date, field_id: str
) -> tuple[list[Item], dict[str, str]]:
    query = urlencode(
        {
            "search_query": cfg["query"],
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": cfg.get("max_results", 100),
        }
    )
    try:
        feed = feedparser.parse(http.get_text(f"{API}?{query}"))
    except Exception as exc:
        return [], {"arxiv": f"{type(exc).__name__}: {exc}"}

    since = datetime.combine(
        run_date - timedelta(days=cfg.get("window_days", 2)), datetime.min.time(), UTC
    )
    items: list[Item] = []
    for entry in feed.entries:
        stamp = entry.get("published_parsed")
        if not stamp:
            continue
        published = datetime(*stamp[:6], tzinfo=UTC)
        if published < since:
            continue
        arxiv_id = re.sub(r"v\d+$", "", entry.id.rsplit("/abs/", 1)[-1])
        items.append(
            Item(
                id=f"arxiv:{arxiv_id}",
                field=field_id,
                source="arxiv",
                title=" ".join(entry.get("title", "").split()),
                url=f"https://arxiv.org/abs/{arxiv_id}",
                published=published.isoformat(),
                summary=" ".join(entry.get("summary", "").split()),
                tags=[tag.get("term", "") for tag in entry.get("tags", [])][:5],
            )
        )
    return items, {}
