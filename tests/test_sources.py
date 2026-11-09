from datetime import date

from intellectism_news import sources as source_module


def test_fetch_all_skips_missing_optional_sources(monkeypatch):
    calls = []

    def fake_rss(cfg, run_date, field_id):
        calls.append("rss")
        return [], {}

    def fake_arxiv(cfg, run_date, field_id):
        calls.append("arxiv")
        return [], {}

    monkeypatch.setattr(source_module.rss, "fetch", fake_rss)
    monkeypatch.setattr(source_module.arxiv, "fetch", fake_arxiv)

    field = {
        "id": "labor",
        "sources": {"rss": {"enabled": True}, "arxiv": {"enabled": True}},
    }
    items, errors = source_module.fetch_all(field, date(2026, 11, 10))
    assert items == []
    assert errors == {}
    assert calls == ["rss", "arxiv"]
