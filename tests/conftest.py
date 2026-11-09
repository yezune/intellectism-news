from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def root() -> Path:
    return ROOT


@pytest.fixture
def config():
    from intellectism_news.config import load_config

    return load_config(ROOT / "config" / "fields.yaml")
