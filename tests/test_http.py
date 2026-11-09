import pytest
import requests

from intellectism_news import http


def test_retry_429_then_ok(monkeypatch):
    calls = []
    sleeps = []

    def transport(url, headers):
        calls.append(url)
        if len(calls) == 1:
            return 429, b""
        return 200, b"ok"

    monkeypatch.setattr(http.time, "sleep", lambda seconds: sleeps.append(seconds))
    http.set_transport(transport)

    assert http.get_bytes("https://example.com") == b"ok"
    assert calls == ["https://example.com", "https://example.com"]
    assert sleeps == [2]
    assert http.retry_events() == [
        {"url": "https://example.com", "attempt": 1, "status": 429, "wait": 2}
    ]


def test_retry_500_then_ok(monkeypatch):
    calls = []

    def transport(url, headers):
        calls.append(url)
        if len(calls) == 1:
            return 500, b""
        return 200, b"ok"

    monkeypatch.setattr(http.time, "sleep", lambda seconds: None)
    http.set_transport(transport)

    assert http.get_bytes("https://example.com") == b"ok"
    assert calls == ["https://example.com", "https://example.com"]


def test_retry_404_is_not_retried(monkeypatch):
    calls = []

    def transport(url, headers):
        calls.append(url)
        return 404, b""

    monkeypatch.setattr(http.time, "sleep", lambda seconds: None)
    http.set_transport(transport)

    with pytest.raises(http.FetchError):
        http.get_bytes("https://example.com")
    assert calls == ["https://example.com"]


def test_timeout_retries(monkeypatch):
    calls = []
    sleeps = []

    def transport(url, headers):
        calls.append(url)
        raise requests.Timeout("slow")

    monkeypatch.setattr(http.time, "sleep", lambda seconds: sleeps.append(seconds))
    http.set_transport(transport)

    with pytest.raises(requests.Timeout):
        http.get_bytes("https://example.com")
    assert len(calls) == 4
    assert sleeps == [2, 5, 10]


def test_default_transport_uses_timeout(monkeypatch):
    seen = {}

    class FakeResponse:
        status_code = 200
        content = b"ok"

    def fake_get(url, headers, timeout):
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(http.requests, "get", fake_get)
    http.set_transport(None)

    assert http.get_bytes("https://example.com") == b"ok"
    assert seen["timeout"] == http.TIMEOUT
