"""HTTP access layer. Tests inject fixtures with set_transport()."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import requests

USER_AGENT = "intellectism-news/0.1"
TIMEOUT = 30
RETRY_STATUS = (429, 500, 502, 503, 504)
BACKOFF_SECONDS = (2, 5, 10)

# (url, headers) -> (status_code, body_bytes)
Transport = Callable[[str, dict[str, str]], tuple[int, bytes]]


class FetchError(RuntimeError):
    def __init__(self, url: str, status: int, attempts: int = 1):
        super().__init__(f"HTTP {status}: {url}")
        self.url = url
        self.status = status
        self.attempts = attempts


def _default_transport(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    response = requests.get(url, headers={"User-Agent": USER_AGENT, **headers}, timeout=TIMEOUT)
    return response.status_code, response.content


_transport: Transport = _default_transport
_cache: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[int, bytes]] = {}
_retry_events: list[dict[str, Any]] = []


def set_transport(transport: Transport | None) -> None:
    global _transport
    _transport = transport or _default_transport
    _cache.clear()
    _retry_events.clear()


def retry_events() -> list[dict[str, Any]]:
    return list(_retry_events)


def reset_retry_events() -> None:
    _retry_events.clear()


def _fetch(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    last_exc: Exception | None = None
    status = 0
    for attempt, wait in enumerate((*BACKOFF_SECONDS, None), start=1):
        try:
            status, body = _transport(url, headers)
        except requests.RequestException as exc:
            last_exc = exc
            if wait is None:
                break
            _retry_events.append(
                {"url": url, "attempt": attempt, "status": None, "wait": wait}
            )
            time.sleep(wait)
            continue
        if status not in RETRY_STATUS:
            return status, body
        if wait is None:
            break
        _retry_events.append({"url": url, "attempt": attempt, "status": status, "wait": wait})
        time.sleep(wait)
    if last_exc is not None:
        raise last_exc
    raise FetchError(url, status, attempts=attempt)


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def get_bytes(url: str, headers: dict[str, str] | None = None) -> bytes:
    key = (url, tuple(sorted((headers or {}).items())))
    if key not in _cache:
        _cache[key] = _fetch(url, headers or {})
    status, body = _cache[key]
    if status not in (200, 206):
        raise FetchError(url, status)
    return body


def get_text(url: str, headers: dict[str, str] | None = None) -> str:
    return get_bytes(url, headers).decode("utf-8", errors="replace")


def get_json(url: str, headers: dict[str, str] | None = None):
    return json.loads(get_bytes(url, headers))
