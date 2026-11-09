"""RSS/Atom feed collector."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

import feedparser

from .. import http
from ..models import Item


def _strip_html(text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", text or "").split())


def fetch(
    cfg: dict[str, Any], run_date: date, field_id: str
) -> tuple[list[Item], dict[str, str]]:
    since = datetime.combine(
        run_date - timedelta(days=cfg.get("window_days", 3)), datetime.min.time(), UTC
    )
    items: list[Item] = []
    errors: dict[str, str] = {}
    for feed_cfg in cfg.get("feeds", []):
        try:
            feed = feedparser.parse(http.get_text(feed_cfg["url"], feed_cfg.get("headers")))
        except Exception as exc:  # one dead feed must not stop the run
            errors[f"rss:{feed_cfg['name']}"] = f"{type(exc).__name__}: {exc}"
            continue
        for entry in feed.entries:
            stamp = entry.get("published_parsed") or entry.get("updated_parsed")
            if not stamp:
                continue
            published = datetime(*stamp[:6], tzinfo=UTC)
            if published < since:
                continue
            link = entry.get("link", "")
            if not link:
                continue
            items.append(
                Item(
                    id=f"url:{hashlib.sha1(link.encode()).hexdigest()[:16]}",
                    field=field_id,
                    source=f"rss:{feed_cfg['name']}",
                    title=" ".join(entry.get("title", "").split()),
                    url=link,
                    published=published.isoformat(),
                    summary=_strip_html(entry.get("summary", ""))[:1200],
                )
            )
    return items, errors
