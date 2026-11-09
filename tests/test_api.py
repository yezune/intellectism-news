import json
from datetime import date

from intellectism_news import http
from intellectism_news.sources import api

PAYLOAD = {
    "results": [
        {
            "title": "AI policy",
            "html_url": "https://example.com/1",
            "publication_date": "2026-11-09",
            "abstract": "A policy document.",
        }
    ]
}


def test_fetch():
    http.set_transport(lambda url, headers: (200, json.dumps(PAYLOAD).encode()))
    items, errors = api.fetch(
        {
            "window_days": 3,
            "sources": [{"name": "Federal Register", "url": "https://example.com/api"}],
        },
        date(2026, 11, 10),
        "policy",
    )
    assert len(items) == 1
    assert items[0].id.startswith("url:")
    assert items[0].source == "api:Federal Register"
    assert items[0].field == "policy"
    assert items[0].url == "https://example.com/1"
    assert items[0].published == "2026-11-09T00:00:00+00:00"
    assert errors == {}


def test_dead():
    def boom(url, headers):
        raise RuntimeError("boom")

    http.set_transport(boom)
    items, errors = api.fetch(
        {
            "window_days": 3,
            "sources": [{"name": "Federal Register", "url": "https://example.com/api"}],
        },
        date(2026, 11, 10),
        "policy",
    )
    assert items == []
    assert "api:Federal Register" in errors


def test_fetch_skips_future_dates():
    payload = {
        "results": [
            {
                "title": "Call for papers",
                "html_url": "https://example.com/future",
                "publication_date": "2027-01-01",
                "abstract": "Not yet published.",
            }
        ]
    }
    http.set_transport(lambda url, headers: (200, json.dumps(payload).encode()))
    items, errors = api.fetch(
        {
            "window_days": 7,
            "sources": [{"name": "OpenAlex", "url": "https://example.com/api"}],
        },
        date(2026, 11, 9),
        "labor",
    )
    assert items == []
    assert errors == {}


def test_fetch_applies_date_filter():
    seen = []

    def transport(url, headers):
        seen.append(url)
        return 200, json.dumps(PAYLOAD).encode()

    http.set_transport(transport)
    items, errors = api.fetch(
        {
            "window_days": 7,
            "sources": [
                {
                    "name": "OpenAlex",
                    "url": "https://example.com/api?search=policy",
                    "date_filter": "from_publication_date:{since},to_publication_date:{until}",
                }
            ],
        },
        date(2026, 11, 9),
        "policy",
    )
    assert len(items) == 1
    assert errors == {}
    assert seen == [
        "https://example.com/api?search=policy"
        "&filter=from_publication_date:2026-11-02,to_publication_date:2026-11-09"
    ]
