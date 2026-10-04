SRCDIR=src
TESTDIR=test
DOCSDIR=docs
SCRIPTSDIR=scripts
CODEDIRS=$(SRCDIR) $(TESTDIR) $(DOCSDIR) $(SCRIPTSDIR)

.DEFAULT_GOAL := check

.PHONY: bootstrap
bootstrap:
	uv sync --dev

.PHONY: check
check: format lint ty

.PHONY: format
format:
	uv run ruff format --check $(CODEDIRS)

.PHONY: lint
lint:
	uv run ruff check $(CODEDIRS)

.PHONY: ty
ty:
	uv run ty check

.PHONY: fix
fix:
	uv run ruff format $(CODEDIRS)
	uv run ruff check --fix $(CODEDIRS)

.PHONY: docs
docs:
	uv run sphinx-build --fail-on-warning --keep-going $(DOCSDIR) $(DOCSDIR)/_build/html

.PHONY: icons
icons:
	uv run $(SCRIPTSDIR)/icons_to_pdf.py

.PHONY: clean
clean:
	git clean -X --force

.PHONY: test
test:
	uv run coverage run --source $(SRCDIR) --module pytest test
	uv run coverage report
	uv run coverage html
