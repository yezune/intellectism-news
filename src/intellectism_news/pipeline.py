"""Daily pipeline: fetch, curate, write JSON, write digest, update state."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from . import http
from .config import get_field, load_config
from .curate import curate
from .models import RunResult
from .render import render_digest
from .sources import fetch_all

README_START = "<!-- LATEST:START -->"
README_END = "<!-- LATEST:END -->"


class Paths:
    def __init__(self, root: Path):
        self.root = root
        self.config = root / "config" / "fields.yaml"
        self.readme = root / "README.md"

    def data_path(self, field: str, d: str) -> Path:
        return self.root / "data" / field / d[:4] / f"{d}.json"

    def digest_path(self, field: str, d: str) -> Path:
        return self.root / "digests" / field / d[:4] / f"{d}.md"

    def state_path(self, field: str) -> Path:
        return self.root / "state" / field / "seen.json"


def today(config: dict[str, Any]) -> date:
    return datetime.now(ZoneInfo(config.get("timezone", "UTC"))).date()


def _replace_block(path: Path, start: str, end: str, body: str) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if start not in text:
        return
    block = f"{start}\n{body}\n{end}"
    text = re.sub(re.escape(start) + ".*?" + re.escape(end), lambda _: block, text, flags=re.S)
    path.write_text(text, encoding="utf-8")


def update_readme(root: Path, run_date: str, field: str, summary: str) -> None:
    readme = root / "README.md"
    if not readme.exists():
        return
    digests = sorted((root / "digests").glob(f"{field}/*/*.md"), reverse=True)[:14]
    recent = "\n".join(f"- [{p.stem}]({p.relative_to(root).as_posix()})" for p in digests)
    body = (
        f"**최신 {field} 다이제스트: [{run_date}](digests/{field}/{run_date[:4]}/{run_date}.md)**"
        f" — {summary}\n\n최근 14일:\n\n{recent}"
    )
    _replace_block(readme, README_START, README_END, body)


def run_daily(
    root: Path, field_id: str, run_date: date | None = None, force: bool = False
) -> Path | None:
    paths = Paths(root)
    config = load_config(paths.config)
    field = get_field(config, field_id)
    run_date = run_date or today(config)
    d = run_date.isoformat()

    digest_path = paths.digest_path(field_id, d)
    if digest_path.exists() and not force:
        return None

    state_path = paths.state_path(field_id)
    seen: dict[str, str] = json.loads(state_path.read_text()) if state_path.exists() else {}

    raw, errors = fetch_all(field, run_date)
    items = curate(raw, field, seen, d)
    for item in items:
        if item.primary_source is None:
            item.primary_source = item.url
    generated_at = http.now_iso()
    result = RunResult(
        date=d,
        field=field_id,
        generated_at=generated_at,
        fetched=len(raw),
        errors=errors,
        items=items,
        candidates=[item.id for item in items],
    )

    data_path = paths.data_path(field_id, d)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8"
    )

    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(
        render_digest(d, field_id, generated_at, items, errors), encoding="utf-8"
    )

    for item in items:
        seen.setdefault(item.id, d)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(dict(sorted(seen.items())), indent=0, ensure_ascii=False), encoding="utf-8"
    )

    update_readme(root, d, field_id, f"후보 {len(items)}건 · 오류 {len(errors)}건")
    return digest_path
