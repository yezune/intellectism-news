PYTHON ?= .venv/bin/python
UV ?= uv
CARGO ?= cargo
INEWS_CORE ?= crates/inews-core/target/debug/inews-core
CARGO_MANIFEST ?= crates/inews-core/Cargo.toml

.PHONY: setup test lint check daily candidates clean

FIELD ?= labor
FORCE ?=
DATE ?=
NORMALIZE_URL ?= https://Example.COM:443/path/?utm_source=x&b=2&a=1\#frag
NORMALIZE_EXPECTED ?= https://example.com/path?a=1&b=2

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
	@test "$$($(INEWS_CORE) normalize '$(NORMALIZE_URL)')" = "$(NORMALIZE_EXPECTED)"
	@for file in $$(find data -name '*.json' 2>/dev/null); do \
		$(INEWS_CORE) validate "$$file"; \
	done

daily:
	$(PYTHON) -m intellectism_news.cli daily --field $(FIELD) $(if $(FORCE),--force)

candidates:
	$(PYTHON) -m intellectism_news.cli candidates --field $(FIELD) $(if $(DATE),--date $(DATE))

clean:
	rm -rf .venv .pytest_cache .ruff_cache
	$(CARGO) clean --manifest-path $(CARGO_MANIFEST)
