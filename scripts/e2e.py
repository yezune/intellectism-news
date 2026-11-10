"""End-to-end run: real collection in a temp root, then schema validation.

By default the run uses a throwaway root. Pass `--root <dir>` to keep the
collected data in that directory (the channel's E2E uses this to read the
handoff JSON).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

from intellectism_news.pipeline import run_daily
from intellectism_news.validate import validate_result

REPO = Path(__file__).resolve().parents[1]
FIELDS = ("labor", "ownership", "policy")
RUN_DATE = date(2026, 11, 9)


def run_e2e(root: Path, run_date: date = RUN_DATE) -> list[dict]:
    """Run all three fields in the given root and return the JSON results."""
    (root / "config").mkdir(parents=True, exist_ok=True)
    if root.resolve() != REPO.resolve():
        shutil.copy(REPO / "config" / "fields.yaml", root / "config" / "fields.yaml")
        shutil.copy(REPO / "README.md", root / "README.md")

    results: list[dict] = []
    for field in FIELDS:
        state = root / "state" / field / "seen.json"
        if state.exists():
            state.unlink()
        digest = run_daily(root, field, run_date, force=True)
        if digest is None:
            raise RuntimeError(f"{field}: digest was not written")
        data = root / "data" / field / run_date.strftime("%Y") / f"{run_date.isoformat()}.json"
        result = json.loads(data.read_text(encoding="utf-8"))
        errors = validate_result(result)
        if errors:
            raise RuntimeError(f"{field}: {errors}")
        if result["errors"]:
            raise RuntimeError(f"{field}: source errors {result['errors']}")
        if not result["candidates"]:
            raise RuntimeError(f"{field}: no candidates")
        results.append(result)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None)
    args = parser.parse_args()

    if args.root:
        results = run_e2e(Path(args.root))
    else:
        with tempfile.TemporaryDirectory(prefix="inews-e2e-") as tmp:
            results = run_e2e(Path(tmp))
    for result in results:
        print(
            f"{result['field']}: {len(result['candidates'])} candidates, "
            f"{len(result['errors'])} errors, {len(result['retries'])} retries"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
