PYTHON ?= .venv/bin/python
UV ?= uv
CARGO ?= cargo
INEWS_CORE ?= crates/inews-core/target/debug/inews-core
CARGO_MANIFEST ?= crates/inews-core/Cargo.toml

.PHONY: setup test lint check daily clean

FIELD ?= labor
FORCE ?=

setup:
	$(UV) venv --python 3.14
	$(UV) lock
	$(UV) sync --extra dev
	$(CARGO) build --manifest-path $(CARGO_MANIFEST)

test:
	$(PYTHON) -m pytest -q
	$(CARGO) test --manifest-path $(CARGO_MANIFEST)

lint:
	$(PYTHON) -m ruff check src tests
	$(CARGO) fmt --manifest-path $(CARGO_MANIFEST) --check
	$(CARGO) clippy --manifest-path $(CARGO_MANIFEST) -- -D warnings

check: test lint
	$(INEWS_CORE) validate tests/fixtures/labor.json

daily:
	$(PYTHON) -m intellectism_news.cli daily --field $(FIELD) $(if $(FORCE),--force)

clean:
	rm -rf .venv .pytest_cache .ruff_cache
	$(CARGO) clean --manifest-path $(CARGO_MANIFEST)
