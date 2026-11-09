from datetime import date

from intellectism_news import http
from intellectism_news.sources import arxiv

ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry><id>http://arxiv.org/abs/2611.12345v1</id>
<title>Labor and Automation</title>
<summary>We study automation and employment.</summary>
<published>2026-11-09T00:00:00Z</published>
<author><name>A</name></author>
<link href="http://arxiv.org/abs/2611.12345v1"/></entry>
<entry><id>http://arxiv.org/abs/2611.00000v1</id>
<title>Old</title>
<summary>Old.</summary>
<published>2026-01-01T00:00:00Z</published>
<author><name>B</name></author>
<link href="http://arxiv.org/abs/2611.00000v1"/></entry>
</feed>"""


def test_fetch():
    http.set_transport(lambda url, headers: (200, ATOM.encode()))
    items, errors = arxiv.fetch(
        {"query": "cat:econ.GN", "window_days": 2, "max_results": 100},
        date(2026, 11, 10),
        "labor",
    )
    assert len(items) == 1
    assert items[0].id == "arxiv:2611.12345"
    assert items[0].source == "arxiv"
    assert items[0].field == "labor"
    assert items[0].url == "https://arxiv.org/abs/2611.12345"
    assert errors == {}


def test_dead():
    def boom(url, headers):
        raise RuntimeError("boom")

    http.set_transport(boom)
    items, errors = arxiv.fetch(
        {"query": "cat:econ.GN", "window_days": 2},
        date(2026, 11, 10),
        "labor",
    )
    assert items == []
    assert "arxiv" in errors
