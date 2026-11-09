"""Command line for intellectism-news."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .config import list_fields, load_config
from .pipeline import Paths, run_daily, today
from .validate import validate_result


def _candidates_markdown(result: dict) -> str:
    items = {item["id"]: item for item in result.get("items", [])}
    lines = [
        f"# {result.get('field', '')} 후보 — {result.get('date', '')}",
        "",
        "| # | score | source | title | primary_source |",
        "|---|---|---|---|---|",
    ]
    for index, candidate_id in enumerate(result.get("candidates", []), 1):
        item = items.get(candidate_id, {})
        title = str(item.get("title", "")).replace("|", "\\|")
        lines.append(
            f"| {index} | {item.get('score', 0)} | {item.get('source', '')} "
            f"| {title} | {item.get('primary_source') or ''} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="intellectism-news")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list fields")

    daily = sub.add_parser("daily", help="run one field")
    daily.add_argument("--field", required=True)
    daily.add_argument("--date", type=date.fromisoformat)
    daily.add_argument("--force", action="store_true")

    check = sub.add_parser("check", help="validate one JSON file")
    check.add_argument("--field", required=True)
    check.add_argument("--date", type=date.fromisoformat)

    candidates = sub.add_parser("candidates", help="show the candidates for one day")
    candidates.add_argument("--field", required=True)
    candidates.add_argument("--date", type=date.fromisoformat)
    candidates.add_argument("--json", action="store_true", help="print the full JSON")

    args = parser.parse_args(argv)
    paths = Paths(args.root)
    config = load_config(paths.config)

    if args.cmd == "list":
        for field in list_fields(config):
            print(field)
        return 0

    if args.cmd == "daily":
        out = run_daily(args.root, args.field, args.date, args.force)
        print(f"생성됨: {out}" if out else "이미 있음; 건너뜀 (--force)")
        return 0

    if args.cmd == "check":
        run_date = args.date or today(config)
        path = paths.data_path(args.field, run_date.isoformat())
        if not path.exists():
            print(f"missing: {path}", file=sys.stderr)
            return 1
        result = json.loads(path.read_text())
        errors = validate_result(result)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print(f"OK {path}")
        return 0

    if args.cmd == "candidates":
        run_date = args.date or today(config)
        path = paths.data_path(args.field, run_date.isoformat())
        if not path.exists():
            print(f"missing: {path}", file=sys.stderr)
            return 1
        result = json.loads(path.read_text())
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(_candidates_markdown(result))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
