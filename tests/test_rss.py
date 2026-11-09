from datetime import date

from intellectism_news import http
from intellectism_news.sources import rss

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test</title>
<item><title>Layoffs at Example</title><link>https://example.com/a</link>
<pubDate>Mon, 09 Nov 2026 00:00:00 GMT</pubDate>
<description>Automation and layoffs.</description></item>
<item><title>Old news</title><link>https://example.com/b</link>
<pubDate>Mon, 01 Jan 2026 00:00:00 GMT</pubDate>
<description>Old.</description></item>
</channel></rss>"""


def test_fetch():
    http.set_transport(lambda url, headers: (200, RSS.encode()))
    items, errors = rss.fetch(
        {
            "window_days": 3,
            "feeds": [{"name": "ILO", "url": "https://example.com/feed", "require_keywords": True}],
        },
        date(2026, 11, 10),
        "labor",
    )
    assert len(items) == 1
    assert items[0].source == "rss:ILO"
    assert items[0].field == "labor"
    assert items[0].id.startswith("url:")
    assert items[0].url == "https://example.com/a"
    assert errors == {}


def test_dead_feed():
    def boom(url, headers):
        raise RuntimeError("boom")

    http.set_transport(boom)
    items, errors = rss.fetch(
        {
            "window_days": 3,
            "feeds": [{"name": "ILO", "url": "https://example.com/feed", "require_keywords": True}],
        },
        date(2026, 11, 10),
        "labor",
    )
    assert items == []
    assert "rss:ILO" in errors
