"""Python mirror of the Rust schema validator."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse


def _is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def validate_result(result: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return ["root must be an object"]

    for key in ("date", "field", "generated_at", "fetched", "errors", "items", "candidates"):
        if key not in result:
            errors.append(f"missing key: {key}")

    date = result.get("date")
    if isinstance(date, str):
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            errors.append("date must be YYYY-MM-DD")
    elif "date" in result:
        errors.append("date must be a string")

    field = result.get("field")
    if isinstance(field, str):
        if not field:
            errors.append("field must not be empty")
    elif "field" in result:
        errors.append("field must be a string")

    generated_at = result.get("generated_at")
    if isinstance(generated_at, str):
        try:
            datetime.fromisoformat(generated_at)
        except ValueError:
            errors.append("generated_at must be RFC 3339")
    elif "generated_at" in result:
        errors.append("generated_at must be a string")

    if "fetched" in result and not isinstance(result["fetched"], int):
        errors.append("fetched must be an integer")
    if "errors" in result and not isinstance(result["errors"], dict):
        errors.append("errors must be an object")

    ids: set[str] = set()
    candidate_flags: dict[str, bool] = {}
    items = result.get("items")
    if isinstance(items, list):
        if len(items) > 20:
            errors.append("items must have at most 20")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"items[{index}] must be an object")
                continue
            for key in (
                "id",
                "field",
                "source",
                "title",
                "url",
                "published",
                "summary",
                "score",
                "tags",
                "candidate",
            ):
                if key not in item:
                    errors.append(f"items[{index}] missing key: {key}")
            item_id = item.get("id")
            if isinstance(item_id, str):
                if item_id in ids:
                    errors.append(f"duplicate id: {item_id}")
                ids.add(item_id)
            elif "id" in item:
                errors.append(f"items[{index}].id must be a string")
            if (
                isinstance(item.get("field"), str)
                and isinstance(field, str)
                and item["field"] != field
            ):
                errors.append(f"items[{index}].field mismatch")
            url = item.get("url")
            if isinstance(url, str):
                if not _is_http_url(url):
                    errors.append(f"items[{index}].url is not a valid http(s) URL")
            elif "url" in item:
                errors.append(f"items[{index}].url must be a string")
            published = item.get("published")
            if isinstance(published, str):
                try:
                    datetime.fromisoformat(published)
                except ValueError:
                    errors.append(f"items[{index}].published must be RFC 3339")
            elif "published" in item:
                errors.append(f"items[{index}].published must be a string")
            score = item.get("score")
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                if score != score or score in (float("inf"), float("-inf")):
                    errors.append(f"items[{index}].score must be finite")
            elif "score" in item:
                errors.append(f"items[{index}].score must be a number")
            tags = item.get("tags")
            if isinstance(tags, list):
                if any(not isinstance(tag, str) for tag in tags):
                    errors.append(f"items[{index}].tags must be strings")
            elif "tags" in item:
                errors.append(f"items[{index}].tags must be an array")
            candidate = item.get("candidate")
            if isinstance(candidate, bool):
                if isinstance(item_id, str):
                    candidate_flags[item_id] = candidate
            elif "candidate" in item:
                errors.append(f"items[{index}].candidate must be a boolean")
            primary = item.get("primary_source")
            if primary is not None:
                if isinstance(primary, str):
                    if not _is_http_url(primary):
                        errors.append(f"items[{index}].primary_source is not a valid http(s) URL")
                elif "primary_source" in item:
                    errors.append(f"items[{index}].primary_source must be a string or null")
    elif "items" in result:
        errors.append("items must be an array")

    candidates = result.get("candidates")
    if isinstance(candidates, list):
        if len(candidates) > 10:
            errors.append("candidates must have at most 10")
        for index, candidate in enumerate(candidates):
            if not isinstance(candidate, str):
                errors.append(f"candidates[{index}] must be a string")
                continue
            if candidate not in ids:
                errors.append(f"candidates[{index}] not in items: {candidate}")
            if candidate_flags.get(candidate) is not True:
                errors.append(f"candidates[{index}] item is not candidate: {candidate}")
    elif "candidates" in result:
        errors.append("candidates must be an array")

    return errors
