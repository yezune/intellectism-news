from datetime import date

from intellectism_news import pipeline
from intellectism_news.models import Item
from scripts.e2e import run_e2e


def make_item(field: str) -> Item:
    return Item(
        id=f"url:{field}",
        field=field,
        source="rss:US DOL",
        title=f"Layoffs and automation in {field}",
        url=f"https://example.com/{field}",
        published="2026-11-09T00:00:00+00:00",
        summary="Workers and wages.",
    )


def test_e2e_runs_three_fields(tmp_path, monkeypatch):
    def fake_fetch(field, run_date):
        return [make_item(field["id"])], {}

    monkeypatch.setattr(pipeline, "fetch_all", fake_fetch)
    results = run_e2e(tmp_path, date(2026, 11, 9))
    assert len(results) == 3
    assert [result["field"] for result in results] == ["labor", "ownership", "policy"]
    for result in results:
        assert result["candidates"] == [f"url:{result['field']}"]
        assert result["errors"] == {}
        assert result["retries"] == []
        assert (tmp_path / "digests" / result["field"] / "2026" / "2026-11-09.md").exists()
