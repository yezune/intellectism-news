# Architecture — intellectism news collector

> **Scope.** This document covers the **public collector** only. `intellectism-news` collects public field news, curates it, and writes validated JSON. The **private channel** — editing, review, broadcast, publishing, and corrections — lives in [`../intellectism/`](../intellectism/). The collector does not produce video, call LLMs, or upload to YouTube.

## 1. Scope

- **Public plane** — `intellectism-news`: collects public field news, curates it, writes validated JSON, and hands off.
- **Private plane** — `intellectism/`: selects candidates, runs LLM/voice/editing, publishes video, and keeps corrections.

The boundary is deliberate: GitHub Actions never sees private keys, and the Mac mini never needs to expose inbound ports.

## 2. Design principles

1. **Public ETL, private compute.** Public collection is deterministic and secret-free. Private enrichment (LLM, voice, rendering) runs locally in `intellectism/`.
2. **A PR is a decision, not a job queue.** A PR is a proposal. The public branch carries public data; the private host writes back only metadata and links.
3. **Artifacts, not secrets.** The handoff is a JSON file, a PR, or an object-storage key — not an API key.
4. **Free tier first.** GitHub Actions, free sources, and free tooling.
5. **TDD.** Write the failing test first, then the smallest code that passes.

## 3. System context

```text
┌──────────────────────────────┐
│ GitHub Actions (public)      │
│  - scheduled collector       │
│  - tests, lint, Rust checks  │
│  - opens public PRs          │
└───────────────┬──────────────┘
                │ raw JSON / digest / PR
                ▼
┌──────────────────────────────┐
│ Git + PR                     │
│  - data/<field>/YYYY/...json │
│  - digests/<field>/...md     │
│  - metadata only             │
└───────────────┬──────────────┘
                │ handoff
                ▼
┌──────────────────────────────┐
│ intellectism/ (private)      │
│  - select 3 candidates       │
│  - LLM, voice, edit          │
│  - Blender, Resolve, ffmpeg  │
│  - publish to YouTube/blog   │
└──────────────────────────────┘
```

The collector stops at the handoff. The private channel is documented in [`../intellectism/ARCHITECTURE.md`](../intellectism/ARCHITECTURE.md).

## 4. Components

| Component | Responsibility | Cost |
|---|---|---|
| GitHub Actions | schedule, tests, lint, public collection | free tier |
| `intellectism-news` | RSS/API/arXiv collection, curation, JSON, digest | MIT |
| `inews-core` | URL normalization + JSON schema validation | Rust, free |
| Python 3.14 | collector runtime | free |

## 5. Data flow

1. **Collect** — GitHub Actions runs `make daily` for labor, ownership, and policy.
2. **Validate** — `inews-core validate` checks every JSON file.
3. **Handoff** — the daily workflow commits `data/`, `digests/`, and `state/`; a public PR carries the change.
4. **Stop** — the collector does not edit, render, or publish. `intellectism/` reads the JSON and takes over.

## 6. Free pipeline

| Workflow | Trigger | Purpose |
|---|---|---|
| `.github/workflows/ci.yml` | PR, push | `make check` — tests, lint, Rust checks |
| `.github/workflows/e2e.yml` | schedule, manual | `make e2e` — real collection in a temp root |
| `.github/workflows/daily.yml` | schedule, manual | `make daily` — production collection and commit |

Local entry points:

- `make e2e` — real collector in a temp root, then validate.
- `make daily` — production collector.
- `make check` — tests, lint, Rust normalize/validate.

No paid APIs are used. The collector has no hardware cost.

## 7. E2E definition

`make e2e` runs:

1. create a temp root;
2. copy `config/fields.yaml` and `README.md`;
3. run `run_daily` for labor, ownership, and policy;
4. validate each JSON with the Python validator;
5. assert `errors == {}` and `candidates >= 1`;
6. print the candidate, error, and retry counts.

This is a real E2E: it uses real RSS/API/arXiv sources and the real curation/validation path. It does not publish or upload.

## 8. Security model

- **No secrets in GitHub Actions.** The public workflow only has `contents: read`.
- **No LLM keys in the collector.** LLM keys live in `intellectism/` on the Mac mini.
- **API keys only.** Free API keys (BLS, EIA, Congress.gov, Companies House) go in GitHub Secrets.
- **Least privilege.** Write-back uses a GitHub App or fine-grained PAT with `contents: write` only.
- **Trusted branches only.** The collector runs code from `main` or maintainer branches, never fork PRs.
- **Audit.** The JSON keeps source URL, candidate ID, score, and retry count.

## 9. Storage

| Asset | Location | Retention |
|---|---|---|
| raw JSON | Git | forever |
| digest | Git | forever |
| state | Git | forever |
| metadata | Git | forever |

Video and audio never enter the collector. The collector does not store binaries.

## 10. Failure modes

| Failure | Handling |
|---|---|
| dead RSS feed | recorded in `errors`; the run continues |
| 429/5xx | retry with 2/5/10s backoff; `retries` recorded |
| OpenAlex budget exhausted | source disabled; Federal Register/RSS still reach 10 |
| API key missing | source disabled; `errors` records the reason |
| collector run fails | CI fails; no partial data is merged |

## 11. Decision log

- **ADR-001** — Public collection in GitHub Actions; private processing in `intellectism/`.
- **ADR-002** — A PR is a public decision unit; no private keys in PRs.
- **ADR-003** — The collector stops at JSON + digest; no video, no LLM, no upload.
- **ADR-004** — OpenAlex is disabled while the free budget is exhausted; re-enable with `enabled: true`.
- **ADR-005** — E2E runs in a temp root; CI never touches the production `data/`.
