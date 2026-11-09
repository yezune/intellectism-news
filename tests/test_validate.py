import json
from pathlib import Path

from intellectism_news.validate import validate_result

ROOT = Path(__file__).resolve().parents[1]


def valid():
    return json.loads((ROOT / "tests" / "fixtures" / "labor.json").read_text())


def test_validate_valid():
    assert validate_result(valid()) == []


def test_validate_missing_items():
    result = valid()
    del result["items"]
    assert validate_result(result)


def test_validate_duplicate_ids():
    result = valid()
    result["items"].append(dict(result["items"][0]))
    assert any("duplicate id" in e for e in validate_result(result))


def test_validate_candidate_not_in_items():
    result = valid()
    result["candidates"] = ["missing"]
    assert any("not in items" in e for e in validate_result(result))


def test_validate_bad_url():
    result = valid()
    result["items"][0]["url"] = "not-a-url"
    assert any("valid http" in e for e in validate_result(result))


def test_validate_bad_date():
    result = valid()
    result["date"] = "2026-13-01"
    assert any("YYYY-MM-DD" in e for e in validate_result(result))


def test_validate_candidate_false():
    result = valid()
    result["items"][0]["candidate"] = False
    assert any("not candidate" in e for e in validate_result(result))
