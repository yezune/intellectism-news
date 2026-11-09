import json
from datetime import date

import yaml

from intellectism_news import pipeline
from intellectism_news.models import Item


def make_item(
    id: str, title: str = "Layoffs", source: str = "rss:ILO", field: str = "labor"
) -> Item:
    return Item(
        id=id,
        field=field,
        source=source,
        title=title,
        url=f"https://example.com/{id}",
        published="2026-11-09T00:00:00+00:00",
        summary="",
    )


def write_config(root):
    (root / "config").mkdir()
    feeds = [{"name": f"Feed{i}", "require_keywords": True} for i in range(12)]
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
                            "rss": {"weight": 1.5, "feeds": feeds},
                            "arxiv": {"weight": 1.0},
                        },
                        "limits": {"candidates": 10, "max_items": 20, "max_per_source": 3},
                    },
                    "ownership": {
                        "name": "소유",
                        "question": "누가 데이터·모델·컴퓨트를 소유하는가",
                        "keywords": {"ownership": 3},
                        "min_relevance": 2,
                        "sources": {
                            "rss": {"weight": 1.5, "feeds": feeds},
                            "arxiv": {"weight": 1.0},
                        },
                        "limits": {"candidates": 10, "max_items": 20, "max_per_source": 3},
                    },
                    "policy": {
                        "name": "정치경제",
                        "question": "누가 규칙을 정하고, 누구에게 비용을 넘기는가",
                        "keywords": {"regulation": 3},
                        "min_relevance": 2,
                        "sources": {
                            "rss": {"weight": 1.5, "feeds": feeds},
                            "arxiv": {"weight": 1.0},
                        },
                        "limits": {"candidates": 10, "max_items": 20, "max_per_source": 3},
                    },
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


def test_run_daily_ownership(tmp_path, monkeypatch):
    write_config(tmp_path)
    items = [
        make_item(f"o{i}", title="Ownership", source=f"rss:Feed{i}", field="ownership")
        for i in range(12)
    ]
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: (items, {}))
    out = pipeline.run_daily(tmp_path, "ownership", date(2026, 11, 10))
    assert out is not None
    data = json.loads((tmp_path / "data" / "ownership" / "2026" / "2026-11-10.json").read_text())
    assert len(data["items"]) == 10
    assert all(item["field"] == "ownership" for item in data["items"])
    assert (tmp_path / "state" / "ownership" / "seen.json").exists()
    assert (tmp_path / "digests" / "ownership" / "2026" / "2026-11-10.md").exists()


def test_run_daily_policy(tmp_path, monkeypatch):
    write_config(tmp_path)
    items = [
        make_item(f"p{i}", title="Regulation", source=f"rss:Feed{i}", field="policy")
        for i in range(12)
    ]
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: (items, {}))
    out = pipeline.run_daily(tmp_path, "policy", date(2026, 11, 10))
    assert out is not None
    data = json.loads((tmp_path / "data" / "policy" / "2026" / "2026-11-10.json").read_text())
    assert len(data["items"]) == 10
    assert all(item["field"] == "policy" for item in data["items"])
    assert (tmp_path / "state" / "policy" / "seen.json").exists()
    assert (tmp_path / "digests" / "policy" / "2026" / "2026-11-10.md").exists()


def test_candidates_sorted_and_primary(tmp_path, monkeypatch):
    write_config(tmp_path)
    items = [
        make_item("rss", title="Layoffs", source="rss:Feed0"),
        make_item("arxiv", title="Layoffs", source="arxiv"),
    ]
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: (items, {}))
    pipeline.run_daily(tmp_path, "labor", date(2026, 11, 10))
    data = json.loads((tmp_path / "data" / "labor" / "2026" / "2026-11-10.json").read_text())
    assert [item["id"] for item in data["items"]] == ["rss", "arxiv"]
    assert all(item["candidate"] for item in data["items"])
    assert all(item["primary_source"] for item in data["items"])
    assert data["candidates"] == ["rss", "arxiv"]
