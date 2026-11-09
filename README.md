# intellectism-news

Field-specific news collectors for the intellectism channel.

One engine, eight field configurations. The first three fields are **labor**, **ownership**, and **policy**.

## What it does

- Fetches RSS feeds and arXiv queries for a field.
- Scores items by relevance, source weight, and freshness.
- Deduplicates by canonical URL.
- Writes up to 10 candidates per day as JSON and a Markdown digest.
- Keeps a per-field seen state so the same item is not repeated.

## Quick start

```sh
make setup
make test
make daily
```

`make daily` runs `intellectism-news daily --field labor`.

Show the latest candidates:

```sh
make daily FIELD=ownership
make candidates FIELD=ownership
```

`candidates` prints Markdown; add `--json` to the CLI to print the full JSON.

## Environment

- Python 3.14 via `.venv`
- Rust 1.98.0 via `rust-toolchain.toml`
- `uv` for the Python environment
- `make` for the entry points

## Layout

```
config/fields.yaml        field definitions (sources, keywords, limits)
src/intellectism_news/    Python engine
crates/inews-core/        Rust validator + URL normalizer
tests/                    pytest fixtures and tests
data/<field>/<YYYY>/      daily JSON
digests/<field>/<YYYY>/   daily Markdown
state/<field>/seen.json   per-field dedup state
```

## Milestones

See [MILESTONES.md](MILESTONES.md). M0–M3 are complete; M4 is next.

## TDD

1. Write the failing test.
2. Run `make test` and see it fail.
3. Write the smallest code that passes.
4. Run `make test`, `make lint`, and `make check`.
5. Commit.

## Free sources

RSS: ILO Jobs, US DOL, EPI, UNI, NBER, SEC, FTC, Federal Register, EUR-Lex, World Bank, IMF, UNCTAD.

APIs: arXiv, OpenAlex, Crossref, SEC EDGAR, Federal Register, BLS, Eurostat, World Bank, GitHub, Hugging Face.

No paid APIs, no scraping.

<!-- LATEST:START -->
**최신 policy 다이제스트: [2026-11-09](digests/policy/2026/2026-11-09.md)** — 후보 1건 · 오류 0건

최근 14일:

- [2026-11-09](digests/policy/2026/2026-11-09.md)
<!-- LATEST:END -->
