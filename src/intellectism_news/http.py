"""HTTP access layer. Tests inject fixtures with set_transport()."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime

import requests

USER_AGENT = "intellectism-news/0.1"
TIMEOUT = 30

# (url, headers) -> (status_code, body_bytes)
Transport = Callable[[str, dict[str, str]], tuple[int, bytes]]


class FetchError(RuntimeError):
    def __init__(self, url: str, status: int):
        super().__init__(f"HTTP {status}: {url}")
        self.url = url
        self.status = status


def _default_transport(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    response = requests.get(url, headers={"User-Agent": USER_AGENT, **headers}, timeout=TIMEOUT)
    return response.status_code, response.content


_transport: Transport = _default_transport
_cache: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[int, bytes]] = {}


def set_transport(transport: Transport | None) -> None:
    global _transport
    _transport = transport or _default_transport
    _cache.clear()


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def get_bytes(url: str, headers: dict[str, str] | None = None) -> bytes:
    key = (url, tuple(sorted((headers or {}).items())))
    if key not in _cache:
        _cache[key] = _transport(url, headers or {})
    status, body = _cache[key]
    if status not in (200, 206):
        raise FetchError(url, status)
    return body


def get_text(url: str, headers: dict[str, str] | None = None) -> str:
    return get_bytes(url, headers).decode("utf-8", errors="replace")


def get_json(url: str, headers: dict[str, str] | None = None):
    return json.loads(get_bytes(url, headers))
