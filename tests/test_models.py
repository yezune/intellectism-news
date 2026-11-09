from intellectism_news.models import Item, RunResult


def test_item_defaults():
    item = Item(
        id="x",
        field="labor",
        source="rss:ILO",
        title="t",
        url="https://e.com",
        published="2026-11-09T00:00:00+00:00",
    )
    assert item.candidate is False
    assert item.score == 0.0
    assert item.tags == []
    assert item.primary_source is None


def test_item_to_dict():
    item = Item(
        id="x",
        field="labor",
        source="rss:ILO",
        title="t",
        url="https://e.com",
        published="2026-11-09T00:00:00+00:00",
    )
    d = item.to_dict()
    assert d["id"] == "x"
    assert d["candidate"] is False
    assert d["primary_source"] is None


def test_run_result_to_dict():
    item = Item(
        id="x",
        field="labor",
        source="rss:ILO",
        title="t",
        url="https://e.com",
        published="2026-11-09T00:00:00+00:00",
    )
    result = RunResult(
        date="2026-11-10",
        field="labor",
        generated_at="2026-11-10T07:17:00+09:00",
        fetched=1,
        errors={},
        items=[item],
        candidates=["x"],
    )
    d = result.to_dict()
    assert d["date"] == "2026-11-10"
    assert d["candidates"] == ["x"]
    assert d["items"][0]["id"] == "x"
    assert d["retries"] == []


def test_run_result_to_dict_includes_retries():
    result = RunResult(
        date="2026-11-10",
        field="labor",
        generated_at="2026-11-10T07:17:00+09:00",
        fetched=1,
        errors={},
        items=[],
        candidates=[],
        retries=[{"url": "https://e.com", "attempt": 1, "status": 429, "wait": 1}],
    )
    assert result.to_dict()["retries"] == [
        {"url": "https://e.com", "attempt": 1, "status": 429, "wait": 1}
    ]
