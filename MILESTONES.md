# Milestones

> Strict TDD. Every milestone starts with a failing test, then the smallest code that makes it pass.
> The Rust core is the stability layer; Python is the collector and curator.

## M0 — Repo and environment

Acceptance:
- [x] `make setup` creates `.venv` (Python 3.14) and builds `crates/inews-core`.
- [x] `make test` passes Python + Rust.
- [x] `make lint` passes.
- [x] `.python-version` and `rust-toolchain.toml` are pinned.

Tests first:
- [x] `tests/test_env.py` — Python version is 3.14, `cargo --version` is 1.98.
- [x] Rust: `crates/inews-core/tests/cli.rs` — `normalize` returns a canonical URL.

## M1 — Schema + labor field

Acceptance:
- [x] `make check` runs `pytest`, `cargo test`, and `inews-core validate` on a fixture.
- [x] `make daily --field labor` writes `data/labor/YYYY/YYYY-MM-DD.json` and `digests/labor/YYYY/YYYY-MM-DD.md`.
- [x] The JSON has 10 candidates in tests (real run: 4 candidates, 0 errors).
- [x] The digest lists the same candidates with source and score.
- [x] Errors from a dead feed are recorded in `errors`, not fatal.

Tests first:
- [x] `test_config.py` — load, validate, unknown field.
- [x] `test_models.py` — `Item`, `RunResult`, `to_dict`.
- [x] `test_curate.py` — relevance, dedup, score, per-source cap, seen.
- [x] `test_rss.py` — fake feed, window, dead feed, error.
- [x] `test_arxiv.py` — fake Atom, window, dedup.
- [x] `test_pipeline.py` — run, skip, force, JSON, digest.
- [x] `test_cli.py` — list, daily, check.
- [x] Rust `validate` — valid, missing key, duplicate id, candidate not in items, bad URL, bad date.

## M2 — ownership and policy fields

Acceptance:
- [x] `config/fields.yaml` has `ownership` and `policy`.
- [x] `make daily FIELD=ownership` and `FIELD=policy` write their own JSON and digest.
- [x] `list` shows all three fields.
- [x] Tests cover 10 candidates per field; real runs currently return 2 and 3 candidates.

Tests first:
- [x] `test_config.py` — all three fields.
- [x] `test_pipeline.py` — each field has its own state and data path.
- [x] `test_sources.py` — optional source blocks are skipped.
- [x] `test_api.py` — Federal Register JSON API.
- [x] `test_curate.py` — `api:` source weight and keyword gate.

## M3 — Candidate integration

Acceptance:
- [x] The daily JSON is the candidate file: `items` is sorted by score, and `candidates` lists the top IDs in the same order.
- [x] Every candidate has `candidate: true` and `primary_source` set to its URL.
- [x] `make check` validates the JSON.
- [x] `intellectism-news candidates --field <field> [--date]` prints the top candidates as Markdown; `--json` prints the full JSON.
- [x] `negative_keywords` filters crime and enforcement noise from `ownership` and `policy`.

Tests first:
- [x] `test_pipeline.py` — candidates are sorted by score, `candidate` is true, `primary_source` is set.
- [x] `test_cli.py` — `candidates` prints Markdown and `candidates --json` prints the JSON.
- [x] `test_curate.py` — negative keywords are excluded.
- [x] `test_validate.py` — Python validator mirrors the Rust validator.

## M4 — GitHub Actions

Acceptance:
- [x] `.github/workflows/daily.yml` runs `make daily` for each field on a schedule.
- [x] It commits `data/`, `digests/`, and `state/`.
- [x] Free tier only (`ubuntu-latest`, `setup-uv`, `rustup`).

Tests first:
- [x] `test_workflow.py` — workflow YAML has three fields and a schedule.

## M5 — Rust core expansion

Acceptance:
- [x] `inews-core normalize` and `validate` are used by `make check`.
- [x] `make check` validates the fixture and every real `data/**/*.json`.
- [x] Python stays the collector: 3 fields collect in about 40 seconds, so a Rust collector is not needed.
- [x] Rust tests cover normalize (tracking, default port, fragment, trailing slash) and validate schema cases.

Tests first:
- [x] Rust `normalize` — tracking, default port, fragment, trailing slash.
- [x] Rust `validate` — all schema cases.
- [x] `test_makefile.py` — `make check` runs `normalize` and `validate`.

## M6 — Stability

Acceptance:
- [x] 3 fields, 10 candidates each, 0 fatal errors.
- [x] Rate limits and retries are recorded in `retries` and the digest.
- [x] `make daily` runs under 5 minutes on the free tier (about 10.7s / 6.0s / 4.8s).

Tests first:
- [x] `test_http.py` — retry, backoff, timeout.
- [x] `test_pipeline.py` — one dead feed does not stop the run.

Implementation:
- [x] `http.py` retries 429/500/502/503/504 with 1/2/4 second backoff and records each event.
- [x] `run_daily` stores `retries` in JSON and renders them in the digest.
- [x] OpenAlex runs three queries per field; Federal Register runs for labor and ownership.
- [x] API windows are 30 days; `max_per_source` is 10 so 10 candidates are reachable.
- [x] `policy` filters biology and health papers with negative keywords.
- [x] OpenAlex is wired with retry/backoff recording; it is temporarily disabled because the free daily budget was exhausted, and can be re-enabled with `enabled: true`.
