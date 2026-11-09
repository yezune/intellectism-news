"""JSON API collector for structured document endpoints."""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from .. import http
from ..models import Item

DEFAULT_FIELDS = {
    "title": "title",
    "url": "html_url",
    "published": "publication_date",
    "summary": "abstract",
}


def fetch(
    cfg: dict[str, Any], run_date: date, field_id: str
) -> tuple[list[Item], dict[str, str]]:
    since = datetime.combine(
        run_date - timedelta(days=cfg.get("window_days", 3)), time.min, UTC
    )
    items: list[Item] = []
    errors: dict[str, str] = {}
    for source in cfg.get("sources", []):
        try:
            data = http.get_json(source["url"], source.get("headers"))
        except Exception as exc:
            errors[f"api:{source['name']}"] = f"{type(exc).__name__}: {exc}"
            continue
        fields = {**DEFAULT_FIELDS, **source.get("fields", {})}
        for row in data.get("results", []):
            title = row.get(fields["title"], "")
            link = row.get(fields["url"], "")
            published = row.get(fields["published"], "")
            if not link or not published:
                continue
            try:
                stamp = datetime.fromisoformat(published)
            except ValueError:
                continue
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=UTC)
            if stamp < since:
                continue
            items.append(
                Item(
                    id=f"url:{hashlib.sha1(link.encode()).hexdigest()[:16]}",
                    field=field_id,
                    source=f"api:{source['name']}",
                    title=" ".join(str(title).split()),
                    url=link,
                    published=stamp.isoformat(),
                    summary=(row.get(fields["summary"], "") or "")[:1200],
                )
            )
    return items, errors
