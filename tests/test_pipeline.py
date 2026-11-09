import json
from datetime import date

import yaml

from intellectism_news import pipeline
from intellectism_news.models import Item


def make_item(id: str, title: str = "Layoffs", source: str = "rss:ILO") -> Item:
    return Item(
        id=id,
        field="labor",
        source=source,
        title=title,
        url=f"https://example.com/{id}",
        published="2026-11-09T00:00:00+00:00",
        summary="",
    )


def write_config(root):
    (root / "config").mkdir()
    (root / "config" / "fields.yaml").write_text(
        yaml.safe_dump(
            {
                "timezone": "Asia/Seoul",
                "fields": {
                    "labor": {
                        "name": "노동",
                        "question": "누가 일하고, 무엇이 대체되는가",
                        "keywords": {"layoffs": 3},
                        "min_relevance": 2,
                        "sources": {
                            "rss": {
                                "weight": 1.5,
                                "feeds": [
                                    {"name": f"Feed{i}", "require_keywords": True}
                                    for i in range(12)
                                ],
                            },
                            "arxiv": {"weight": 1.0},
                        },
                        "limits": {"candidates": 10, "max_items": 20, "max_per_source": 3},
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def test_run_daily(tmp_path, monkeypatch):
    write_config(tmp_path)
    items = [make_item(f"x{i}", source=f"rss:Feed{i}") for i in range(12)]
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: (items, {}))
    out = pipeline.run_daily(tmp_path, "labor", date(2026, 11, 10))
    assert out is not None
    data = json.loads((tmp_path / "data" / "labor" / "2026" / "2026-11-10.json").read_text())
    assert len(data["items"]) == 10
    assert len(data["candidates"]) == 10
    assert all(item["candidate"] for item in data["items"])
    assert (tmp_path / "state" / "labor" / "seen.json").exists()
    assert (tmp_path / "digests" / "labor" / "2026" / "2026-11-10.md").exists()


def test_run_daily_skips(tmp_path, monkeypatch):
    write_config(tmp_path)
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: ([make_item("x")], {}))
    first = pipeline.run_daily(tmp_path, "labor", date(2026, 11, 10))
    second = pipeline.run_daily(tmp_path, "labor", date(2026, 11, 10))
    assert first is not None
    assert second is None


def test_run_daily_force(tmp_path, monkeypatch):
    write_config(tmp_path)
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: ([make_item("x")], {}))
    first = pipeline.run_daily(tmp_path, "labor", date(2026, 11, 10))
    second = pipeline.run_daily(tmp_path, "labor", date(2026, 11, 10), force=True)
    assert first is not None
    assert second is not None


def test_run_daily_records_errors(tmp_path, monkeypatch):
    write_config(tmp_path)
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: ([], {"rss:ILO": "boom"}))
    out = pipeline.run_daily(tmp_path, "labor", date(2026, 11, 10))
    assert out is not None
    data = json.loads((tmp_path / "data" / "labor" / "2026" / "2026-11-10.json").read_text())
    assert data["errors"] == {"rss:ILO": "boom"}
    assert data["items"] == []
    assert "boom" in (tmp_path / "digests" / "labor" / "2026" / "2026-11-10.md").read_text()
