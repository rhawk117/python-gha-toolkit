SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

UV := uv
QUALITY := ./scripts/quality.sh

.DEFAULT_GOAL := help

.PHONY: help
help:
	@printf '%s\n' \
		'Targets:' \
		'  format       Format Python, shell, and Markdown files' \
		'  lint         Run all read-only quality checks' \
		'  check        Format first, then run read-only checks' \
		'  test         Run the pytest suite' \
		'  pre-commit   Run the complete pre-commit stage' \
		'  hooks        Install all configured Git hooks'

.PHONY: format
format:
	$(QUALITY) --format

.PHONY: lint
lint:
	$(QUALITY) --check

.PHONY: check
check:
	$(QUALITY) --format --check

.PHONY: test
test:
	$(UV) run --frozen --group test \
		pytest

.PHONY: pre-commit
pre-commit:
	$(UV) run --frozen --group check \
		pre-commit run --all-files --show-diff-on-failure

.PHONY: hooks
pre-commit.hooks:
	$(UV) run --group check \
		pre-commit install --install-hooks