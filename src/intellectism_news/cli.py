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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
