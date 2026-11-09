from intellectism_news.curate import (
    curate,
    merge_duplicates,
    relevance,
    requires_keywords,
    score,
)
from intellectism_news.models import Item


def make_item(
    id: str,
    title: str,
    source: str = "rss:ILO",
    summary: str = "",
    url: str = "https://example.com",
    field: str = "labor",
    published: str = "2026-11-09T00:00:00+00:00",
) -> Item:
    return Item(
        id=id,
        field=field,
        source=source,
        title=title,
        url=url,
        published=published,
        summary=summary,
    )


def cfg(**overrides):
    base = {
        "keywords": {"layoffs": 3, "automation": 3},
        "min_relevance": 2,
        "sources": {
            "rss": {"weight": 1.5, "feeds": [{"name": "ILO", "require_keywords": True}]},
            "arxiv": {"weight": 1.0},
            "api": {
                "weight": 1.5,
                "sources": [{"name": "Federal Register", "require_keywords": True}],
            },
        },
        "limits": {"candidates": 10, "max_items": 20, "max_per_source": 3},
    }
    base.update(overrides)
    return base


def test_relevance():
    assert relevance(make_item("x", "Layoffs and automation"), cfg()["keywords"]) == 6


def test_merge_duplicates():
    a = make_item("x", "A", "rss:ILO", "summary a")
    b = make_item("x", "B", "rss:US DOL", "summary b is longer")
    merged = merge_duplicates([a, b])
    assert len(merged) == 1
    assert merged[0].id == "x"
    assert merged[0].summary == "summary b is longer"


def test_curate_filters_seen():
    items = [make_item("x", "Layoffs"), make_item("y", "Layoffs")]
    out = curate(items, cfg(), {"x": "2026-11-09"}, "2026-11-10")
    assert [i.id for i in out] == ["y"]


def test_curate_keeps_seen_today():
    items = [make_item("x", "Layoffs")]
    out = curate(items, cfg(), {"x": "2026-11-10"}, "2026-11-10")
    assert [i.id for i in out] == ["x"]


def test_curate_filters_low_relevance():
    items = [make_item("x", "Sports")]
    out = curate(items, cfg(), {}, "2026-11-10")
    assert out == []


def test_curate_per_source_cap():
    items = [make_item(f"x{i}", "Layoffs") for i in range(5)]
    out = curate(items, cfg(), {}, "2026-11-10")
    assert len(out) == 3


def test_curate_candidate_limit():
    items = [make_item(f"x{i}", "Layoffs", source=f"rss:Feed{i}") for i in range(20)]
    config = cfg()
    config["sources"]["rss"]["feeds"] = [
        {"name": f"Feed{i}", "require_keywords": True} for i in range(20)
    ]
    out = curate(items, config, {}, "2026-11-10")
    assert len(out) == 10


def test_curate_sets_candidate():
    items = [make_item("x", "Layoffs")]
    out = curate(items, cfg(), {}, "2026-11-10")
    assert all(i.candidate for i in out)


def test_score():
    item = make_item("x", "Layoffs")
    assert score(item, cfg()) == 3.75


def test_source_weight_api():
    item = make_item("x", "Regulation", source="api:Federal Register")
    assert score(item, cfg()) == 1.5


def test_requires_keywords_api():
    item = make_item("x", "Regulation", source="api:Federal Register")
    assert requires_keywords(item, cfg()) is True
