from pathlib import Path

import pytest

from intellectism_news.config import get_field, list_fields, load_config, validate_config

ROOT = Path(__file__).resolve().parents[1]


def test_load_config():
    cfg = load_config(ROOT / "config" / "fields.yaml")
    assert cfg["timezone"] == "Asia/Seoul"
    assert "labor" in cfg["fields"]


def test_validate_config():
    cfg = load_config(ROOT / "config" / "fields.yaml")
    validate_config(cfg)


def test_get_field():
    cfg = load_config(ROOT / "config" / "fields.yaml")
    field = get_field(cfg, "labor")
    assert field["id"] == "labor"
    assert field["name"] == "노동"
    assert field["sources"]["rss"]["enabled"] is True


def test_unknown_field():
    cfg = load_config(ROOT / "config" / "fields.yaml")
    with pytest.raises(KeyError):
        get_field(cfg, "nope")


def test_validate_config_rejects_missing_key():
    cfg = {"fields": {"labor": {"name": "x"}}}
    with pytest.raises(ValueError):
        validate_config(cfg)


def test_list_fields():
    cfg = load_config(ROOT / "config" / "fields.yaml")
    assert list_fields(cfg) == ["labor"]
