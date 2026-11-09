"""Markdown digest rendering."""

from __future__ import annotations

from typing import Any

from .models import Item


def _md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_digest(
    run_date: str,
    field: str,
    generated_at: str,
    items: list[Item],
    errors: dict[str, str],
    retries: list[dict[str, Any]] | None = None,
) -> str:
    retries = retries or []
    lines = [
        f"# {field} 후보 — {run_date}",
        "",
        f"생성 {generated_at} · 후보 {len(items)}건 · 오류 {len(errors)}건 "
        f"· 재시도 {len(retries)}건",
        "",
    ]
    if errors:
        lines += ["## 오류", ""]
        for source, message in sorted(errors.items()):
            lines.append(f"- `{source}`: {message}")
        lines.append("")
    if retries:
        lines += ["## 재시도", ""]
        for event in retries:
            lines.append(
                f"- `{event.get('url', '')}`: {event.get('status', 'timeout')} "
                f"· {event.get('wait', 0)}초"
            )
        lines.append("")
    if not items:
        lines += ["오늘은 후보가 없습니다.", ""]
        return "\n".join(lines)
    lines += ["## 후보", ""]
    for index, item in enumerate(items, 1):
        lines.append(f"### {index}. [{_md(item.title)}]({item.url})")
        lines.append("")
        lines.append(f"_출처: {item.source} · 점수 {item.score:g} · {item.published[:10]}_")
        lines.append("")
        if item.summary:
            summary = (
                item.summary
                if len(item.summary) <= 400
                else item.summary[:400].rsplit(" ", 1)[0] + " …"
            )
            lines += [f"> {summary}", ""]
        if item.primary_source:
            lines += [f"- 1차 자료: {item.primary_source}", ""]
    return "\n".join(lines)
